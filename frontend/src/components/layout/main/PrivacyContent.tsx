import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Checkbox from "@mui/material/Checkbox";
import FormControlLabel from "@mui/material/FormControlLabel";
import Link from "@mui/material/Link";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import React from "react";

/**
 * Displays the S717 privacy collection notice content with acceptance controls.
 *
 * The content structure mirrors the source notice so reviewers can validate wording,
 * bullet points, and links before final legal sign-off.
 *
 * Includes a checkbox for explicit consent and action buttons to accept or decline.
 */
export function PrivacyContent({
    onAgree,
    onDecline,
}: {
    onAgree: () => Promise<void>;
    onDecline: () => void;
}) {
    const [isAccepted, setIsAccepted] = React.useState<boolean>(false);
    return (
        <Box>
            <Box sx={{ maxHeight: "60vh", overflowY: "auto", mb: 2, pr: 1 }}>
            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                The Department of Biodiversity, Conservation and Attractions (DBCA) collects personal information in order to:
            </Typography>

            <Box component="ul" sx={{ pl: 3, mb: 2, color: "text.secondary", listStyleType: "disc" }}>
                <li>
                    <Typography variant="body2" color="textSecondary">
                        Receive, assess and manage animal ethics submissions and approvals in accordance with <em>section 8 of the Animal Welfare Act 2002 (WA)</em>
                    </Typography>
                </li>
                <li>
                    <Typography variant="body2" color="textSecondary">
                        Assess and determine applications made under sections 40 and 45 of the <em>Biodiversity Conservation Act 2016 (WA)</em>
                    </Typography>
                </li>
                <li>
                    <Typography variant="body2" color="textSecondary">
                        Administer, monitor and enforce authorisations, permits and approvals issued by DBCA
                    </Typography>
                </li>
                <li>
                    <Typography variant="body2" color="textSecondary">
                        Communicate with applicants, nominees, researchers, licence holders and authorised representatives regarding applications, approvals, compliance matters or related enquiries
                    </Typography>
                </li>
                <li>
                    <Typography variant="body2" color="textSecondary">
                        Meet DBCA's statutory obligations for record-keeping, reporting, audit and regulatory compliance.
                    </Typography>
                </li>
            </Box>

            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                The personal information collected may include names, contact details, organisational affiliation, role details and other information necessary to assess applications and administer approvals.
            </Typography>

            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                DBCA may share this information:
            </Typography>

            <Box component="ul" sx={{ pl: 3, mb: 2, color: "text.secondary", listStyleType: "disc" }}>
                <li>
                    <Typography variant="body2" color="textSecondary">
                        Internally within DBCA for assessment, decision-making, compliance, audit and operational purposes
                    </Typography>
                </li>
                <li>
                    <Typography variant="body2" color="textSecondary">
                        With relevant advisory bodies, committees or experts (including the Animal Ethics Committee) for the purpose of evaluating applications and submissions
                    </Typography>
                </li>
                <li>
                    <Typography variant="body2" color="textSecondary">
                        With other Western Australian public sector agencies or oversight bodies where required or authorised under the <em>Privacy and Responsible Information Sharing Act 2024 (WA)</em>, the <em>Biodiversity Conservation Act 2016 (WA)</em>, the <em>Animal Welfare Act 2002 (WA)</em>, or other written law.
                    </Typography>
                </li>
            </Box>

            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                You are required to provide this information where it is necessary to enable DBCA to assess applications and submissions and to perform its statutory functions under the <em>Biodiversity Conservation Act 2016 (WA)</em> and the <em>Animal Welfare Act 2002 (WA)</em>.
            </Typography>

            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                If you choose not to provide the required personal information, DBCA may be unable to assess your application or submission, issue an approval or authorisation, or progress the matter further.
            </Typography>

            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                DBCA will handle all personal information in accordance with the <em>Privacy and Responsible Information Sharing Act 2024 (WA)</em> and DBCA's Privacy Policy.
            </Typography>

            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                For further details on how DBCA manages your personal information, please refer to DBCA's Privacy Policy.
            </Typography>

            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                If you have any questions about how your personal information will be handled, or if you would like to access or correct your personal information, please contact DBCA on <strong>(08) 9219 9004</strong> or email <Link href="mailto:privacy@dbca.wa.gov.au">privacy@dbca.wa.gov.au</Link>.
            </Typography>

            </Box>

            <FormControlLabel
                control={(
                    <Checkbox
                        checked={isAccepted}
                        onChange={(_event, checked) => setIsAccepted(checked)}
                    />
                )}
                label="I acknowledge that DBCA will collect, use and disclose my personal information in accordance with applicable privacy laws and DBCA's Privacy Policy."
            />

            <Stack direction="row" spacing={2} sx={{ mt: 2, justifyContent: "space-between" }}>
                <Button
                    variant="outlined"
                    color="inherit"
                    onClick={onDecline}
                >I decline</Button>
                <Button
                    variant="contained"
                    color="primary"
                    disabled={!isAccepted}
                    onClick={onAgree}
                >I agree</Button>
            </Stack>
        </Box>
    );
}
