import TextField from "@mui/material/TextField";


export default function TextInput({
    label,
    isRequired,
    description,
}: Readonly<{
    label: string;
    isRequired: boolean;
    description?: string;
}>) {
    return <TextField
        label={label}
        // defaultValue="Default Value"
        helperText={description}
        required={isRequired}
        variant="outlined"
        className="w-full"
    />
}