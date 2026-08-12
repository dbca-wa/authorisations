# Cross-Tab State Synchronization Issue

## Problem Statement

When a user submits an application in one browser tab, background tabs that display the "My Applications" list do not reflect the updated application status. This creates a stale data problem where the user sees outdated information if they return to the background tab after submission.

### Concrete Scenario

1. User has "My Applications" page open in **Tab A** showing:
   - Application: "Draft" status
   - Action button: "Continue"

2. User opens a NEW tab (**Tab B**) and loads the application form for submission

3. User submits the application successfully in **Tab B**
   - Application status changes to "SUBMITTED" in backend
   - Tab B is closed by user

4. User returns to **Tab A** (which was in background the entire time):
   - Still displays: "Draft" status
   - Still shows: "Continue" button
   - No API call was triggered (component was inactive)
   - Data is stale

### Root Cause

- "My Applications" component in Tab A loaded the application list once and cached it in component state
- Tab A never made another API call while it was in the background
- No mechanism exists to invalidate the local cache when Tab B modifies the backend
- React component retains old state in memory; there's no cross-tab communication

---

## Solution: BroadcastChannel API

### Overview

The **BroadcastChannel API** allows different browser contexts (tabs, windows, iframes) to communicate bidirectionally. When an application is submitted in one tab, that tab broadcasts a message to all other tabs listening on the same channel. Those tabs can then invalidate their cache and re-fetch updated data.

### How It Works

```
┌─────────────────────┐                    ┌─────────────────────┐
│   Tab A             │                    │   Tab B             │
│ (My Applications)   │                    │ (Form Submission)   │
│                     │                    │                     │
│ BroadcastChannel    │◄──────Message──────│ BroadcastChannel    │
│ listening           │  "appSubmitted"    │ sender              │
│                     │                    │                     │
│ Cache invalidated   │                    │ submitApplication() │
│ API re-fetch        │                    │ → broadcasts event  │
│ UI updates          │                    │                     │
└─────────────────────┘                    └─────────────────────┘
```

### Implementation Details

#### 1. Create BroadcastChannel Utility

**File:** `frontend/src/context/BroadcastChannelManager.ts`

```typescript
const CHANNEL_NAME = 'authorisations-app-state';

export const BroadcastChannelManager = {
  /**
   * Broadcast an application submission event to other tabs.
   * Called after successful submission in the form tab.
   */
  broadcastApplicationSubmitted(applicationKey: string): void {
    try {
      const channel = new BroadcastChannel(CHANNEL_NAME);
      channel.postMessage({
        event: 'applicationSubmitted',
        applicationKey,
        timestamp: Date.now(),
      });
      channel.close();
    } catch (error) {
      console.warn('BroadcastChannel not available:', error);
      // Graceful degradation: older browsers simply won't sync
    }
  },

  /**
   * Listen for application state changes from other tabs.
   * Call this once in components that display application lists.
   * Returns unsubscribe function.
   */
  listenForApplicationChanges(
    callback: (applicationKey: string) => void
  ): () => void {
    try {
      const channel = new BroadcastChannel(CHANNEL_NAME);
      
      const handler = (event: MessageEvent) => {
        if (event.data?.event === 'applicationSubmitted') {
          callback(event.data.applicationKey);
        }
      };

      channel.addEventListener('message', handler);

      return () => {
        channel.removeEventListener('message', handler);
        channel.close();
      };
    } catch (error) {
      console.warn('BroadcastChannel not available:', error);
      return () => {}; // No-op cleanup for older browsers
    }
  },
};
```

#### 2. Update Form Submission Handler

**File:** `frontend/src/components/layout/form/FormReviewPage.tsx`

In the `onFinalSubmit()` method, after successful submission:

```typescript
.then((resp) => {
  setUserCanEdit(false);
  
  // Broadcast to other tabs that this application was submitted
  BroadcastChannelManager.broadcastApplicationSubmitted(applicationKey);
  
  // Show success modal (not snackbar)
  showSubmissionSuccessModal();
  
  // Fire confetti
  fireConfettiEffect(5);
  
  return resp;
})
```

#### 3. Update My Applications Component

**File:** `frontend/src/components/layout/main/MyApplications.tsx` (or equivalent)

In the component's useEffect hook:

```typescript
useEffect(() => {
  // Listen for submission events from other tabs
  const unsubscribe = BroadcastChannelManager.listenForApplicationChanges(
    (applicationKey: string) => {
      // Invalidate cache and re-fetch applications
      ApiManager.clearApplicationsCache();
      // Component will re-fetch on next render or manually trigger refetch
      refetchApplications();
    }
  );

  return unsubscribe; // Cleanup listener on unmount
}, []);
```

### Benefits

✅ **Real-time sync** across all tabs  
✅ **Minimal API overhead** — only calls affected components' refresh  
✅ **Supports multiple windows** — works across browser windows too  
✅ **Targeted invalidation** — only affected applications refresh  
✅ **No server infrastructure changes** — pure client-side  
✅ **Graceful degradation** — older browsers simply won't sync (acceptable)  

### Browser Support

- ✅ Chrome/Edge 54+
- ✅ Firefox 38+
- ✅ Safari 15.1+
- ⚠️ Older browsers: silent graceful degradation (no sync, but app still works)

### Additional Use Cases

This mechanism also solves other scenarios:

- **Same application open in multiple tabs:** User edits answers in Tab A, submits → Tab B automatically refreshes to show "SUBMITTED" instead of "DRAFT"
- **Concurrent reviewers:** Multiple reviewer tabs all see updated application queues in real-time
- **Admin operations:** Backend state changes (e.g., status updates by other users) could be broadcast via server → all client tabs
- **Future scaling:** Can extend to broadcast other application state changes (approval, rejection, etc.)

### Testing Considerations

When testing cross-tab behavior:
- Mock `BroadcastChannel` in unit tests
- E2E tests can verify message broadcasting and cache invalidation
- Manual testing: open app in two tabs, submit in one, verify other tab updates

