import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import Accordion from "@mui/material/Accordion";
import AccordionDetails from "@mui/material/AccordionDetails";
import AccordionSummary from "@mui/material/AccordionSummary";
import Link from "@mui/material/Link";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";

import type { ReactNode } from "react";


/**
 * A simple wrapper for consistent privacy statement body text spacing and colour.
 */
const PolicyParagraph = ({ children }: { children: ReactNode }) => {
    return (
        <Typography variant="body2" color="textSecondary">
            {children}
        </Typography>
    );
};

/**
 * Renders bullet-point lists used by multiple policy sections.
 */
const PolicyList = ({ items }: { items: string[] }) => {
    return (
        <List className="list-disc! pl-8! py-0!">
            {items.map((item) => (
                <ListItem key={item} className="list-item! p-1!">
                    <PolicyParagraph>{item}</PolicyParagraph>
                </ListItem>
            ))}
        </List>
    );
};

/**
 * Shared accordion shell to keep section interactions and visual style consistent.
 */
const PrivacyStatementAccordionSection = ({
    title,
    children,
}: {
    title: string;
    children: ReactNode;
}) => {
    return (
        <Accordion disableGutters className="min-h-20 rounded-sm! border border-slate-200 shadow-sm! before:hidden">
            <AccordionSummary
                id={`${title}-header`}
                expandIcon={<ExpandMoreIcon />}
                aria-controls={`${title}-content`}
            >
                <Typography variant="h6" className="font-semibold">
                    {title}
                </Typography>
            </AccordionSummary>
            <AccordionDetails className="border-t border-slate-100 p-4! space-y-4!">
                {children}
            </AccordionDetails>
        </Accordion>
    );
};

/**
 * Displays the Overview as non-collapsible content as requested.
 */
const PrivacyStatementOverviewSection = () => {
    return (
        <Box className="rounded-lg border border-slate-200 bg-slate-50 p-8 space-y-4!">
            <Typography variant="h5" className="font-semibold">
                Overview
            </Typography>
            <PolicyParagraph>
                This Privacy Statement explains how the Authorisations System collects, uses, stores and discloses
                personal information.
            </PolicyParagraph>
            <PolicyParagraph>
                This statement applies only to information collected through the Authorisations System. The
                Authorisations System is provided and maintained by the Ecoinformatics Team within the Biodiversity and
                Conservation Science division of the Department of Biodiversity, Conservations and Attractions (DBCA).
            </PolicyParagraph>
            <PolicyParagraph>
                This statement should be read together with DBCA&apos;s Corporate Privacy Statement, which explains how
                personal information is managed across DBCA&apos;s broader functions.
            </PolicyParagraph>
        </Box>
    );
};

/**
 * Describes what personal information is collected for Authorisations System workflows.
 */
const WhatInformationWeCollectSection = () => {
    const collectedInformationItems = [
        "your name and contact details;",
        "organisation, position or affiliation;",
        "information relating to authorised representatives or nominees;",
        "information contained in applications, supporting documents and correspondence;",
        "payment or invoicing information where applicable; and",
        "any other information reasonably required to assess, administer or monitor an application or approval.",
    ];

    return (
        <PrivacyStatementAccordionSection title="What information do we collect?">
            <PolicyParagraph>
                The Authorisations System collects personal information that is reasonably necessary to assess
                applications and submissions, administer approvals, and support DBCA&apos;s statutory functions.
            </PolicyParagraph>
            <PolicyParagraph>Depending on your application, this may include:</PolicyParagraph>
            <PolicyList items={collectedInformationItems} />
            <PolicyParagraph>
                Some information requested through the Authorisations System is mandatory. If you choose not to provide required
                information, the Authorisations System may be unable to assess your application or submission, issue an
                approval or authorisation, or progress the matter further.
            </PolicyParagraph>
        </PrivacyStatementAccordionSection>
    );
};

/**
 * Explains technical data automatically captured when users interact with the Authorisations System.
 */
const InformationCollectedAutomaticallySection = () => {
    const automaticallyCollectedItems = [
        "your Internet Protocol (IP) address;",
        "browser type and version;",
        "operating system;",
        "device identifiers;",
        "date and time of access;",
        "pages viewed;",
        "documents downloaded;",
        "referring website; and",
        "information collected through cookies and similar technologies.",
    ];
    const technicalUseItems = [
        "operate and maintain the Authorisations System;",
        "protect the security and integrity of the system;",
        "diagnose technical issues;",
        "monitor portal performance;",
        "improve functionality and user experience; and",
        "produce statistical and analytical information to improve our online services.",
    ];

    return (
        <PrivacyStatementAccordionSection title="Information collected automatically">
            <PolicyParagraph>
                When you access the Authorisations System, certain technical information is collected automatically.
            </PolicyParagraph>
            <PolicyParagraph>This may include:</PolicyParagraph>
            <PolicyList items={automaticallyCollectedItems} />
            <PolicyParagraph>This information is collected to:</PolicyParagraph>
            <PolicyList items={technicalUseItems} />
            <PolicyParagraph>
                Cookies do not generally identify you personally. However, where cookie information is linked with
                other information collected through your use of the Authorisations System, it will be handled as
                personal
                information.
            </PolicyParagraph>
            <PolicyParagraph>
                The Authorisations System does not use information collected through this website to make solely
                automated decisions about applications. All application decisions remain subject to assessment by
                authorised officers.
            </PolicyParagraph>
        </PrivacyStatementAccordionSection>
    );
};

/**
 * Outlines the lawful and operational purposes for which personal information is used.
 */
const HowWeUseYourInformationSection = () => {
    const useItems = [
        "assess and determine applications, licences, permits, approvals and exemptions;",
        "administer and monitor approvals and authorised activities;",
        "communicate with applicants, researchers, licence holders and authorised representatives;",
        "undertake compliance, audit and enforcement activities;",
        "maintain records required under legislation; and",
        "perform DBCA's statutory functions under applicable legislation.",
    ];

    return (
        <PrivacyStatementAccordionSection title="How we use your information">
            <PolicyParagraph>Personal information collected through the Authorisations System is used to:</PolicyParagraph>
            <PolicyList items={useItems} />
            <PolicyParagraph>
                Your personal information will only be used for these purposes or another purpose authorised or
                required by law.
            </PolicyParagraph>
        </PrivacyStatementAccordionSection>
    );
};

/**
 * Lists circumstances in which personal information may be shared with other parties.
 */
const SharingYourInformationSection = () => {
    const sharingItems = [
        "within DBCA for assessment, decision-making, compliance, operational and administrative purposes;",
        "to relevant advisory bodies, committees, technical experts or external specialists where required to assess applications and submissions;",
        "to the Department of Primary Industries and Regional Development (DPIRD) where required or authorised by law, including for functions under the Fish Resources Management Act 1994 (WA);",
        "to other Western Australian public sector agencies, regulators or oversight bodies where authorised or required by law, including under the Privacy and Responsible Information Sharing Act 2024 (WA) and other written laws.",
    ];

    return (
        <PrivacyStatementAccordionSection title="Sharing your information">
            <PolicyParagraph>
                Personal information collected through the Authorisations System may be shared:
            </PolicyParagraph>
            <PolicyList items={sharingItems} />
            <PolicyParagraph>
                Personal information is only shared where authorised or required by law and reasonable steps are taken
                to ensure that information is disclosed securely.
            </PolicyParagraph>
        </PrivacyStatementAccordionSection>
    );
};

/**
 * Describes storage, security controls, and how users can request access or corrections.
 */
const StorageSecurityAndAccessSection = () => {
    return (
        <PrivacyStatementAccordionSection title="Storage and security">
            <PolicyParagraph>
                The Authorisations System applies reasonable measures to protect personal information from misuse,
                loss and unauthorised access, modification or disclosure.
            </PolicyParagraph>
            <PolicyParagraph>
                Personal information collected through the Authorisations System may be stored in secure DBCA
                information systems or trusted service providers engaged to support business operations. Information is
                managed in accordance with applicable legislation, information security requirements and recordkeeping
                obligations.
            </PolicyParagraph>

            <Typography variant="subtitle1" className="font-semibold">
                Accessing or correcting your information
            </Typography>
            <PolicyParagraph>
                You may request access to, or correction of, your personal information held through the Authorisations
                System and by DBCA, subject to
                applicable legislation.
            </PolicyParagraph>
            <PolicyParagraph>
                If you have questions about how your personal information is handled, or wish to request access to or
                correction of your personal information, please contact from the information provided in the "Contact
                Information" section below.
            </PolicyParagraph>
        </PrivacyStatementAccordionSection>
    );
};

/**
 * Explains how updates to the privacy statement are published.
 */
const ChangesToPrivacyStatementSection = () => {
    return (
        <PrivacyStatementAccordionSection title="Changes to this Privacy Statement">
            <PolicyParagraph>
                Ecoinformatics may update this Privacy Statement from time to time to reflect changes to legislation,
                business processes, or the functionality of the Authorisations System. The most current version will
                always be available through this website.
            </PolicyParagraph>
        </PrivacyStatementAccordionSection>
    );
};

/**
 * Points users to broader organisation-wide privacy information.
 */
const FurtherInformationSection = () => {
    return (
        <PrivacyStatementAccordionSection title="Further information">
            <PolicyParagraph>
                Further information about how DBCA manages personal information is available in DBCA&apos;s Corporate
                Privacy Statement:
            </PolicyParagraph>
            <List className="list-disc! pl-8! py-0!">
                <ListItem className="list-item! p-1!">
                    <Link
                        href="https://www.dbca.wa.gov.au/privacy"
                        target="_blank"
                        rel="noopener noreferrer"
                        color="inherit"
                        underline="always"
                    >
                        DBCA Corporate Privacy Statement
                    </Link>
                </ListItem>
                <ListItem className="list-item! p-1!">
                    <Link
                        href="https://www.dbca.wa.gov.au/media/6324/download"
                        target="_blank"
                        rel="noopener noreferrer"
                        color="inherit"
                        underline="always"
                    >
                        DBCA Privacy of Personal Information Statement (PDF)
                    </Link>
                </ListItem>
            </List>

        </PrivacyStatementAccordionSection>
    );
};

/**
 * Restates the collection notice acknowledgement language shown during application creation.
 */
const CollectionNoticeAcknowledgementSection = () => {
    return (
        <PrivacyStatementAccordionSection title="Collection Notice acknowledgement">
            <PolicyParagraph>
                By using this website, you acknowledge and agree that your personal information may be collected, used,
                stored and disclosed in accordance with this Privacy Statement, applicable privacy legislation, and
                DBCA&apos;s Corporate Privacy Statement.
            </PolicyParagraph>
        </PrivacyStatementAccordionSection>
    );
};


/**
 * Presents contact details for privacy enquiries.
 */
const ContactInformationSection = () => {
    return (
        <PrivacyStatementAccordionSection title="Contact information">
            <PolicyParagraph>
                For privacy enquiries about the Authorisations System, contact the Ecoinformatics Team at{" "}
                <Link href="mailto:ecoinformatics.admin@dbca.wa.gov.au" underline="hover">
                    ecoinformatics.admin@dbca.wa.gov.au
                </Link>
                .
            </PolicyParagraph>
            <PolicyParagraph>
                You can also contact DBCA Privacy at{" "}
                <Link href="mailto:privacy@dbca.wa.gov.au" underline="hover">
                    privacy@dbca.wa.gov.au
                </Link>
                .
            </PolicyParagraph>
        </PrivacyStatementAccordionSection>
    );
};


/**
 * Renders the standalone privacy statement page content for navigation routes.
 */
export const PrivacyStatement = () => {
    return (
        <Box className="p-8 w-full min-w-4xl lg:w-4xl xl:w-5xl 2xl:w-6xl space-y-4">
            <Typography variant="h4" gutterBottom>
                Privacy Statement
            </Typography>

            <PrivacyStatementOverviewSection />
            <WhatInformationWeCollectSection />
            <InformationCollectedAutomaticallySection />
            <HowWeUseYourInformationSection />
            <SharingYourInformationSection />
            <StorageSecurityAndAccessSection />
            <ChangesToPrivacyStatementSection />
            <FurtherInformationSection />
            <CollectionNoticeAcknowledgementSection />
            <ContactInformationSection />
        </Box>
    );
};
