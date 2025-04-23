
export default function Page() {
    return (
        <div className="min-h-screen bg-gray-100 flex items-center justify-center">
            <form className="max-w-4xl mx-auto p-8 bg-white shadow-lg rounded-lg">
                {/* Section 1: Personal Information */}
                <section className="mb-8">
                    <h2 className="text-2xl font-bold mb-4">Personal Information</h2>
                    <div className="mb-6">
                        <label htmlFor="fullName" className="block text-sm font-medium text-gray-700">Full Name:</label>
                        <p className="text-gray-500 mb-2">Please enter your full legal name as it appears on your government-issued ID.</p>
                        <input type="text" id="fullName" name="fullName" className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500" />
                    </div>
                    <div className="mb-6">
                        <label htmlFor="dob" className="block text-sm font-medium text-gray-700">Date of Birth:</label>
                        <p className="text-gray-500 mb-2">Provide your date of birth in the format MM/DD/YYYY.</p>
                        <input type="date" id="dob" name="dob" className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500" />
                    </div>
                    <div className="mb-6">
                        <label htmlFor="address" className="block text-sm font-medium text-gray-700">Address:</label>
                        <p className="text-gray-500 mb-2">Enter your current residential address including street, city, state, and zip code.</p>
                        <input type="text" id="address" name="address" className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500" />
                    </div>
                </section>

                {/* Section 2: Employment Details */}
                <section className="mb-8">
                    <h2 className="text-2xl font-bold mb-4">Employment Details</h2>
                    <div className="mb-6">
                        <label htmlFor="currentEmployer" className="block text-sm font-medium text-gray-700">Current Employer:</label>
                        <p className="text-gray-500 mb-2">Please provide the name of your current employer or indicate if you are self-employed or unemployed.</p>
                        <input type="text" id="currentEmployer" name="currentEmployer" className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500" />
                    </div>
                    <div className="mb-6">
                        <label htmlFor="jobTitle" className="block text-sm font-medium text-gray-700">Job Title:</label>
                        <p className="text-gray-500 mb-2">Enter your current job title or position.</p>
                        <input type="text" id="jobTitle" name="jobTitle" className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500" />
                    </div>
                    <div className="mb-6">
                        <label htmlFor="employmentDuration" className="block text-sm font-medium text-gray-700">Duration of Employment:</label>
                        <p className="text-gray-500 mb-2">Specify the duration of your current employment in years and months.</p>
                        <input type="text" id="employmentDuration" name="employmentDuration" className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500" />
                    </div>
                </section>

                {/* Section 3: Educational Background */}
                <section className="mb-8">
                    <h2 className="text-2xl font-bold mb-4">Educational Background</h2>
                    <div className="mb-6">
                        <label htmlFor="highestDegree" className="block text-sm font-medium text-gray-700">Highest Degree Obtained:</label>
                        <p className="text-gray-500 mb-2">Please provide the highest degree you have obtained and the institution from which you graduated.</p>
                        <input type="text" id="highestDegree" name="highestDegree" className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500" />
                    </div>
                    <div className="mb-6">
                        <label htmlFor="graduationYear" className="block text-sm font-medium text-gray-700">Year of Graduation:</label>
                        <p className="text-gray-500 mb-2">Enter the year you graduated from your highest degree program.</p>
                        <input type="number" id="graduationYear" name="graduationYear" className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500" />
                    </div>
                    <div className="mb-6">
                        <label htmlFor="major" className="block text-sm font-medium text-gray-700">Major/Field of Study:</label>
                        <p className="text-gray-500 mb-2">Specify your major or field of study for your highest degree.</p>
                        <input type="text" id="major" name="major" className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500" />
                    </div>
                </section>

                {/* Section 4: Project Details */}
                <section className="mb-8">
                    <h2 className="text-2xl font-bold mb-4">Project Details</h2>
                    <div className="mb-6">
                        <label htmlFor="projectTitle" className="block text-sm font-medium text-gray-700">Project Title:</label>
                        <p className="text-gray-500 mb-2">Provide the title of the project you are currently working on or planning to work on.</p>
                        <input type="text" id="projectTitle" name="projectTitle" className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500" />
                    </div>
                    <div className="mb-6">
                        <label htmlFor="projectDescription" className="block text-sm font-medium text-gray-700">Project Description:</label>
                        <p className="text-gray-500 mb-2">Describe the project in detail, including its objectives, methodologies, and expected outcomes.</p>
                        <textarea id="projectDescription" name="projectDescription" rows={4} className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"></textarea>
                    </div>
                    <div className="mb-6">
                        <label htmlFor="projectDuration" className="block text-sm font-medium text-gray-700">Project Duration:</label>
                        <p className="text-gray-500 mb-2">Specify the expected duration of the project in months or years.</p>
                        <input type="text" id="projectDuration" name="projectDuration" className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500" />
                    </div>
                </section>

                <div className="text-center">
                    <button type="submit" className="px-6 py-2 bg-indigo-600 text-white font-medium rounded-md shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                        Submit
                    </button>
                </div>
            </form>
        </div>

    );
}
