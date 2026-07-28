import Box from "@mui/material/Box";
import Link from "@mui/material/Link";
import Typography from "@mui/material/Typography";
import LaunchIcon from "@mui/icons-material/Launch";

/**
 * Displays the S717 privacy collection notice content.
 *
 * The content structure mirrors the source notice so reviewers can validate wording,
 * bullet points, and links before final legal sign-off.
 */
export const PrivacyContent = () => {
    return (
        <>
            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                The Department of Biodiversity, Conservation and Attractions (DBCA) collects personal information to:
            </Typography>

            <ul className="pl-6 mb-4 text-inherit list-disc">
                <li>
                    <Typography variant="body2" color="textSecondary">
                        receive, assess and manage animal ethics submissions and approvals in accordance with section 8 of the <em>Animal Welfare Act 2002</em> (WA) (AW Act);
                    </Typography>
                </li>
                <li>
                    <Typography variant="body2" color="textSecondary">
                        assess and determine applications made under sections 40 and 45 of the <em>Biodiversity Conservation Act 2016</em> (WA) (BC Act);
                    </Typography>
                </li>
                <li>
                    <Typography variant="body2" color="textSecondary">
                        assess and determine applications made under regulation 89 of the <em>Conservation and Land Management Regulations 2002</em> (WA) (CALM Regulations);
                    </Typography>
                </li>
                <li>
                    <Typography variant="body2" color="textSecondary">
                        administer, monitor and enforce other authorisations, permits and approvals that it issues;
                    </Typography>
                </li>
                <li>
                    <Typography variant="body2" color="textSecondary">
                        communicate with applicants, nominees, researchers, licence holders and authorised representatives regarding applications, approvals, compliance matters or related enquiries; and
                    </Typography>
                </li>
                <li>
                    <Typography variant="body2" color="textSecondary">
                        meet its statutory obligations for record-keeping, reporting, audit and regulatory compliance.
                    </Typography>
                </li>
            </ul>

            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                The personal information collected may include names, contact details, organisational affiliation, role details and other information necessary to assess applications and issue lawful authority for activities.
            </Typography>

            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                DBCA may share this information:
            </Typography>

            <ul className="pl-6 mb-4 text-inherit list-disc">
                <li>
                    <Typography variant="body2" color="textSecondary">
                        internally within DBCA for assessment, decision-making, compliance, audit and operational purposes;
                    </Typography>
                </li>
                <li>
                    <Typography variant="body2" color="textSecondary">
                        with relevant advisory bodies, committees or experts (including the <em>Animal Ethics Committee</em>) for the purpose of evaluating applications and submissions;
                    </Typography>
                </li>
                <li>
                    <Typography variant="body2" color="textSecondary">
                        with the <em>Department of Primary Industries and Regional Development</em> (DPIRD) for the purpose of assessing and determining exemptions under section 7 of the <em>Fish Resources Management Act 1994</em> (WA) (FRMA Act), including in some cases the application of biodiversity conservation conditions for the purposes of section 7(2)(b) of the BC Act; and
                    </Typography>
                </li>
                <li>
                    <Typography variant="body2" color="textSecondary">
                        with other Western Australian public sector agencies or oversight bodies where required or authorised under the <em>Privacy and Responsible Information Sharing Act 2024</em> (WA) (PRIS Act), the BC Act, the AW Act, the <em>Conservation and Land Management Act 1984</em> (WA) (CALM Act), or any other written law.
                    </Typography>
                </li>
            </ul>

            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                You are required to provide this information where it is necessary to enable DBCA to assess applications and submissions and to perform its statutory functions under the BC Act, the AW Act, the CALM Act, the CALM Regulations and to support DPIRD's statutory functions under the FRMA Act.
            </Typography>

            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                If you choose not to provide the required personal information, DBCA may be unable to assess your application or submission, issue an approval or authorisation, or progress the matter further.
            </Typography>

            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                DBCA will handle all personal information in accordance with the PRIS Act and DBCA's Privacy Policy.
            </Typography>

            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                For further details on how DBCA manages your personal information, please refer to <Link href="https://www.dbca.wa.gov.au/privacy" target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1">DBCA's Privacy Policy<LaunchIcon fontSize="inherit" /></Link>.
            </Typography>

            <Typography variant="body2" color="textSecondary" sx={{ mb: 0 }}>
                If you have any questions about how your personal information will be handled, or if you would like to access or correct your personal information, please contact DBCA at email <Link href="mailto:privacy@dbca.wa.gov.au">privacy@dbca.wa.gov.au</Link>.
            </Typography>
        </>
    );
}

/**
 * Renders the standalone privacy policy page content for navigation routes.
 */
export const PrivacyPolicy = () => {
    return (
        <Box className="p-8 w-full min-w-4xl lg:w-4xl xl:w-5xl 2xl:w-6xl">
            <Typography variant="h4" gutterBottom>
                Privacy Policy
            </Typography>
            <PrivacyContent />
        </Box>
    );
};
