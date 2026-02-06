import CancelOutlinedIcon from '@mui/icons-material/CancelOutlined';
import DeleteIcon from '@mui/icons-material/Delete';
import Badge from "@mui/material/Badge";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { getIconFromFilename } from "../context/Utils";
import type { IApplicationAttachment } from "../context/types/Application";
import IconButton from '@mui/material/IconButton';


function dummyDeleteAttachment(attachment: IApplicationAttachment) {
    // TODO: Replace with actual API call
    alert(`Delete attachment: ${attachment.name}`);
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
        <Stack direction="row" spacing={4} marginTop={2}>
            {attachments.map((attachment, aIdx) => (
                <Box key={attachment.key + aIdx} className="relative p-4 border border-gray-300 rounded-md bg-gray-50 flex flex-col items-center justify-center" style={{ minWidth: 100, minHeight: 120 }}>
                    <a
                        href={attachment.download_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ textDecoration: 'none', display: 'flex', flexDirection: 'column', alignItems: 'center', position: 'relative' }}
                    >
                        {/* File type icon with delete badge if allowed */}
                        <span style={{ position: 'relative', display: 'inline-block' }}>
                            {canDelete ? (
                                <Badge
                                    color="error"
                                    overlap="circular"
                                    badgeContent={(
                                        <Box>
                                            {/* <IconButton
                                                size="small"
                                                color="inherit"
                                                onClick={e => { e.preventDefault(); dummyDeleteAttachment(attachment); }}
                                                aria-label={`Delete ${attachment.name}`}
                                                style={{ padding: 0 }}
                                            >
                                                Delete
                                                <CancelOutlinedIcon style={{ cursor: 'pointer', fontSize: 18 }} />
                                            </IconButton> */}
                                            <CancelOutlinedIcon style={{ cursor: 'pointer', fontSize: 18 }} onClick={e => { e.preventDefault(); dummyDeleteAttachment(attachment); }} />
                                        </Box>
                                    )}
                                    anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
                                >
                                    {getIconFromFilename(attachment.name)}
                                </Badge>
                            ) : (
                                getIconFromFilename(attachment.name)
                            )}
                        </span>
                        {/* File name below icon */}
                        <Typography className="mt-2 text-blue-600 underline" variant="body2" style={{ wordBreak: 'break-all', textAlign: 'center', maxWidth: 200 }}>
                            {attachment.name}
                        </Typography>
                    </a>
                </Box>
            ))}
        </Stack>
    );
};
