import { isValidElement } from 'react'
import { describe, expect, it, vi } from 'vitest'

import { getIconFromFilename, scrollToQuestion } from './Utils'

/**
 * Verify file icons stay aligned with the extension-to-icon mapping contract.
 */
const testGetIconFromFilenameReturnsThePdfIconClass = () => {
  const icon = getIconFromFilename('application.PDF')

  // Narrow unknown to a React element with typed props before reading props.
  if (!isValidElement<{ className?: string }>(icon)) {
    throw new Error('Expected getIconFromFilename to return a React element.')
  }

  expect(icon.props.className).toContain('vscode-icons--file-type-pdf2')
}

/**
 * Verify question scrolling targets the deterministic DOM id used by the form.
 */
const testScrollToQuestionScrollsTheResolvedQuestionIntoView = () => {
  const target = document.createElement('div')
  const scrollIntoView = vi.fn()

  target.id = 'q-2.1-3'
  Object.defineProperty(target, 'scrollIntoView', {
    value: scrollIntoView,
    configurable: true,
  })
  document.body.appendChild(target)

  try {
    scrollToQuestion({ stepIndex: 2, sectionIndex: 1, questionIndex: 3 })

    expect(scrollIntoView).toHaveBeenCalledWith({
      behavior: 'smooth',
      block: 'center',
    })
  } finally {
    target.remove()
  }
}

describe('Utils', () => {
  it('returns the PDF icon class for PDF filenames', testGetIconFromFilenameReturnsThePdfIconClass)
  it('scrolls the resolved question element into view', testScrollToQuestionScrollsTheResolvedQuestionIntoView)
})