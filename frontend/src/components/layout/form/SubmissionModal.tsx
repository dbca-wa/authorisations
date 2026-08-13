import CloseIcon from '@mui/icons-material/Close';
import ExitToAppIcon from '@mui/icons-material/ExitToApp';
import DoneAllRoundedIcon from '@mui/icons-material/DoneAllRounded';
import DownloadIcon from '@mui/icons-material/Download';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';

/**
 * Modal displayed after successful application submission.
 * Confirms submission status, explains next steps, and provides download option.
 */
export function SubmissionModal({
  open,
  applicationKey,
  onClose,
}: {
  open: boolean;
  applicationKey: string;
  onClose: () => void;
}) {
  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle className="flex items-center justify-between">
        <Box className="flex items-center gap-2">
          <DoneAllRoundedIcon color="success" />
          <span>Application Successfully Submitted</span>
        </Box>
        <IconButton size="small" onClick={onClose} aria-label="close">
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent className="space-y-6!">
        <Typography>
          This application is now locked in read-only mode.
        </Typography>

        <Typography variant="body2" sx={{ color: 'text.secondary' }}>
          You will be able to track the progress of your application from the "My Applications" page. Any additional information or requests for clarification will be sent to your registered email address.
        </Typography>

        <Box className="flex gap-2 justify-center">
          <Button
            variant="outlined"
            color="primary"
            startIcon={<DownloadIcon />}
            href={`/d/${applicationKey}`}
          >
            Download PDF
          </Button>
          <Button
            variant="outlined"
            color="secondary"
            startIcon={<ExitToAppIcon />}
            onClick={window.close}
          >
            Exit application
          </Button>
        </Box>
      </DialogContent>
    </Dialog>
  );
}
