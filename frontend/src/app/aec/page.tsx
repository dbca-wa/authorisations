"use client";
import React from "react";
import Button from "@mui/material/Button";
import FormControlLabel from "@mui/material/FormControlLabel";
import Checkbox from "@mui/material/Checkbox";
import { StepsContext } from "../common/steps";

export default function Page() {
    const { activeStep, setActiveStep } = React.useContext(StepsContext); // Destructure activeStep and setActiveStep
    console.log("Context in Page:", { activeStep, setActiveStep });
    
    const handleNext = () => {
        console.log("Current step:", activeStep);
        setActiveStep((prevStep) => prevStep + 1); // Update the step
    };

    return (
        <div className="mt-4 bg-gray-300 p-8 rounded-lg shadow-lg w-full max-w-5xl">
            <form className="mx-auto p-8 bg-white shadow-lg rounded-lg">
                <h2 className="text-2xl font-bold mb-4 text-center">Terms of Service</h2>
                <p className="mb-6">Please answer all sections thoroughly and in plain English and ensure all acronyms are defined the first time they are used. The information provided in this application should support the case for ethical acceptability of the project and allow the AEC to assess the project in relation to requirements of the Code. </p>
                <FormControlLabel control={<Checkbox />} label="I agree to terms of service" />
                <div className="text-center">
                    <Button variant="contained" onClick={handleNext}>
                        Continue
                    </Button>
                </div>
            </form>
        </div>
    );
}
