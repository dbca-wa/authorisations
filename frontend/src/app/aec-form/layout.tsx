import ApplicationSteps from './steps';

const steps = [
    {
        label: 'Terms of Service',
        description: 'Read and accept the terms of service.',
    },
    {
        label: 'Scientific Review',
        description: 'Submit your project for scientific review.',
    },
    {
        label: 'Competencies & Declarations',
        description: 'Provide your competencies and declarations.',
    },
    {
        label: 'Project Details',
        description: 'Fill in the details of your project.',
    },
    {
        label: 'Replacement',
        description: 'Describe how you will replace animals in your project.',
    },
    {
        label: 'Reduction',
        description: 'Explain how you will reduce the number of animals used.',
    },
    {
        label: 'Refinement',
        description: 'Outline how you will refine your methods to minimize suffering.',
    },
];

// 2 column layout with steps on the left and form on the right
export default function FormLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {

    return (
        <div className="flex flex-col md:flex-row">
            <div className="md:w-1/3 p-4 bg-gray-100">
                <h2 className="text-2xl font-bold mb-4">Application Steps</h2>
                <ApplicationSteps steps={steps} />
            </div>
            <div className="md:w-2/3 p-4 bg-white shadow-lg rounded-lg">
                {children}
            </div>
        </div>
    );
}