import CancelOutlinedIcon from '@mui/icons-material/CancelOutlined';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import DownloadIcon from '@mui/icons-material/Download';
import Badge from "@mui/material/Badge";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { getIconFromFilename } from "../context/Utils";
import type { IApplicationAttachment } from "../context/types/Application";
import IconButton from '@mui/material/IconButton';
import Link from '@mui/material/Link';
import { Button, ButtonGroup, Icon } from '@mui/material';


function dummyDeleteAttachment(attachment: IApplicationAttachment) {
    // TODO: Replace with actual API call
    alert(`Delete attachment: ${attachment.name}`);
}

function dummyRenameAttachment(attachment: IApplicationAttachment) {
    alert(`Rename attachment: ${attachment.name}`);
}


export const FileAttachmentList = ({
    attachments,
    canDelete = false,
}: {
    attachments: IApplicationAttachment[];
    canDelete?: boolean;
}) => {
    return (
        // <CancelOutlinedIcon style={{ cursor: 'pointer', fontSize: 18 }} onClick={e => { e.preventDefault(); dummyDeleteAttachment(attachment); }} />
        <Box className="p-4 border border-gray-300 rounded-md">
            <Stack direction="row" spacing={4} marginTop={2} justifyContent={"center"} alignItems={"center"} >
                {attachments.map((attachment) => (
                    <Box className="relative border border-gray-300 rounded-lg px-4 pb-8 flex flex-col items-center min-w-[120px]">
                        {canDelete && (
                            <Box className="absolute bottom-0 center-x-0 flex gap-1">
                                <IconButton
                                    color="error"
                                    size="small"
                                    title={`Delete: ${attachment.name}`}
                                    onClick={() => dummyDeleteAttachment(attachment)}
                                >
                                    <DeleteIcon fontSize="small" />
                                </IconButton>
                                <IconButton
                                    color="primary"
                                    size="small"
                                    title={`Rename: ${attachment.name}`}
                                    onClick={() => dummyRenameAttachment(attachment)}
                                >
                                    <EditIcon fontSize="small" />
                                </IconButton>
                            </Box>
                        )}
                        <Link
                            href={attachment.download_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            underline="none"
                            color="textPrimary"
                            className="flex flex-col items-center gap-2"
                        >
                            {getIconFromFilename(attachment.name)}
                            <Typography variant="body2" style={{ wordBreak: 'break-word', textAlign: 'center', maxWidth: 120 }}>
                                {attachment.name}
                            </Typography>
                        </Link>
                    </Box>
                ))}
            </Stack>
        </Box>
    );
};
