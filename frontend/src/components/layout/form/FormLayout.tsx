import ExitToAppIcon from '@mui/icons-material/ExitToApp';
import MenuIcon from '@mui/icons-material/Menu';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import SaveIcon from '@mui/icons-material/Save';
import MuiAppBar, { type AppBarProps as MuiAppBarProps } from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import React from 'react';

import { styled } from '@mui/material/styles';
import type { FieldValues, SubmitHandler, UseFormProps } from 'react-hook-form';
import { FormProvider, useForm } from 'react-hook-form';
import { useLoaderData, useNavigate, type NavigateFunction } from 'react-router';
import { DRAWER_WIDTH } from '../../../context/Constants';
import { LocalStorage } from '../../../context/LocalStorage';
import type { IAnswers, IApplicationData } from '../../../context/types/Application';
import type { IQuestionnaire, IQuestionnaireData } from '../../../context/types/Questionnaire';
import { FormReviewPage } from './FormReviewPage';
import { FormSidebar } from './FormSidebar';
import { scrollToTop } from '../../../context/Utils';
import { FormActiveStep } from './FormActiveStep';


export const FormLayout = () => {
    // Fetch application and questionnaire from API
    const { app, questionnaire } =
        useLoaderData<{ app: IApplicationData, questionnaire: IQuestionnaireData }>();

    // Load stored answers from local storage
    const storedAnswers = React.useMemo<IAnswers>(
        () => LocalStorage.getAnswers(app.key), []
    );

    // Drawer state
    const [drawerOpen, setDrawerOpen] = React.useState<boolean>(true);

    // Manage activeStep state here
    const [stepIndex, setActiveStep] = React.useState<number>(0);

    // Form methods & state
    const formParams: UseFormProps<IAnswers> = {
        defaultValues: storedAnswers,
        // We do custom scroll, see onError function when submit
        shouldFocusError: false,
    };
    const formMethods = useForm<FieldValues>(formParams);

    const handleBack = (): void => {
        // Store form values before going back
        LocalStorage.setAnswers(app.key, formMethods.getValues());

        setActiveStep((prevStep) => prevStep - 1);
    };

    const handleContinue: SubmitHandler<FieldValues> = (data) => {
        // console.log("Form data:", data)

        // Save answers to local storage
        LocalStorage.setAnswers(app.key, data);

        // Next step (or the review page)
        setActiveStep((prevStep) => prevStep + 1);
    }

    // Account menu state and handlers
    const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);

    // Change page title
    React.useEffect(() => {
        document.title = `${app.questionnaire_name} : DBCA Authorisations`;
    }, [app.questionnaire_name]);

    return (
        <Box sx={{ display: 'flex' }}>
            <AppBar position="fixed" open={drawerOpen}>
                <Toolbar>
                    <IconButton
                        color="inherit"
                        aria-label="open drawer"
                        onClick={() => setDrawerOpen(!drawerOpen)}
                        edge="start"
                        sx={[
                            { marginRight: 5 },
                            drawerOpen && { display: 'none' },
                        ]}
                    >
                        <MenuIcon />
                    </IconButton>
                    <Typography variant="h6" noWrap component="div">
                        {app.questionnaire_name}
                    </Typography>
                    <AccountMenu
                        anchorEl={anchorEl}
                        setAnchorEl={setAnchorEl}
                    />
                </Toolbar>
            </AppBar>
            <FormSidebar
                steps={questionnaire.document.steps}
                activeStep={stepIndex}
                drawerOpen={drawerOpen}
                setDrawerOpen={setDrawerOpen}
            />
            <Box component="main" sx={{ marginTop: "64px", p: 2 }}>
                <FormProvider {...formMethods}>
                    <FormLayoutContent
                        handleBack={handleBack}
                        handleContinue={handleContinue}
                        questionnaire={questionnaire.document}
                        stepIndex={stepIndex}
                    />
                </FormProvider>
            </Box>
        </Box>
    );
}


interface AppBarProps extends MuiAppBarProps {
    open?: boolean;
}


const AppBar = styled(MuiAppBar, {
    shouldForwardProp: (prop) => prop !== 'open',
})<AppBarProps>(({ theme }) => ({
    zIndex: theme.zIndex.drawer + 1,
    transition: theme.transitions.create(['width', 'margin'], {
        easing: theme.transitions.easing.sharp,
        duration: theme.transitions.duration.leavingScreen,
    }),
    variants: [
        {
            props: ({ open }) => open,
            style: {
                marginLeft: DRAWER_WIDTH,
                width: `calc(100% - ${DRAWER_WIDTH}px)`,
                transition: theme.transitions.create(['width', 'margin'], {
                    easing: theme.transitions.easing.sharp,
                    duration: theme.transitions.duration.enteringScreen,
                }),
            },
        },
    ],
}));


const AccountMenu = ({
    anchorEl, setAnchorEl,
}: {
    anchorEl: null | HTMLElement;
    setAnchorEl: React.Dispatch<React.SetStateAction<null | HTMLElement>>;
}) => {
    const handleMenu = (event: React.MouseEvent<HTMLElement>) => setAnchorEl(event.currentTarget);
    const handleClose = () => setAnchorEl(null);
    const navigate: NavigateFunction = useNavigate();

    return (
        <Box sx={{ marginLeft: 'auto' }}>
            <IconButton
                size="large"
                aria-label="account of current user"
                aria-controls="menu-appbar"
                aria-haspopup="true"
                onClick={handleMenu}
                color="inherit"
            >
                <MoreVertIcon />
            </IconButton>
            <Menu
                id="menu-appbar"
                anchorEl={anchorEl}
                anchorOrigin={{
                    vertical: 'bottom',
                    horizontal: 'right',
                }}
                keepMounted
                transformOrigin={{
                    vertical: 'top',
                    horizontal: 'right',
                }}
                open={Boolean(anchorEl)}
                onClose={handleClose}
                sx={{
                    '& .MuiMenuItem-root': { gap: 1.5 }
                    , '& .MuiSvgIcon-root': { fontSize: 'inherit' }
                }}
            >
                <MenuItem
                    onClick={() => {
                        console.log("Saving application")
                        handleClose();
                    }}
                >
                    <SaveIcon /> Save
                </MenuItem>
                <MenuItem
                    onClick={() => {
                        // Assuming we're in a popup window
                        window.close();

                        // If we are not in a popup, we can navigate to my applications
                        if (!window.closed) {
                            handleClose();
                            navigate("/my-applications", { replace: true })
                        }
                    }}
                >
                    <ExitToAppIcon /> Exit
                </MenuItem>
            </Menu>
        </Box>
    )
}


const FormLayoutContent = ({
    handleBack,
    handleContinue,
    questionnaire, stepIndex,
}: {
    handleBack: () => void;
    handleContinue: SubmitHandler<FieldValues>;
    questionnaire: IQuestionnaire;
    stepIndex: number;
}) => {
    scrollToTop([stepIndex]);

    // We are on the review page
    if (stepIndex === questionnaire.steps.length) {
        return (
            <FormReviewPage
                questionnaire={questionnaire}
                onBack={handleBack}
            />
        );
    }

    return (
        <FormActiveStep
            handleBack={handleBack}
            handleContinue={handleContinue}
            currentStep={questionnaire.steps[stepIndex]}
            stepIndex={stepIndex}
        />
    );
}
