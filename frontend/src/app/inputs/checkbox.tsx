import Checkbox from "@mui/material/Checkbox";
import FormControlLabel from "@mui/material/FormControlLabel";

export default function CheckboxInput({
    label,
    isRequired,
}: Readonly<{
    label: string;
    isRequired: boolean;
}>) {
    return <FormControlLabel control={<Checkbox />}
        label={label}
        required={isRequired}
        className="w-full"
    />
}