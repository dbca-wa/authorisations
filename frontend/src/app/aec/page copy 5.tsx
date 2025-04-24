
export default function Page() {
    return (
        <div className="min-h-screen flex items-center justify-center">
            <main className="bg-gray-300  p-8 rounded-lg shadow-lg w-full max-w-5xl">
                <h1 className="text-2xl font-bold mb-6 text-center">Terms of Service</h1>
                
                <form className="max-w-6xl mx-auto p-8 bg-white shadow-lg rounded-lg">
                    {/* Section 1: Project Information */}
                    <section className="mb-8">
                        <h2 className="text-2xl font-bold mb-4">Project Information</h2>
                        <div className="mb-6">
                            <label htmlFor="projectTitle" className="block text-sm font-medium text-gray-700">Project Title:</label>
                            <input type="text" id="projectTitle" name="projectTitle" className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500" />
                        </div>
                        <div className="mb-6">
                            <label htmlFor="chiefInvestigator" className="block text-sm font-medium text-gray-700">Chief Investigator (CI):</label>
                            <input type="text" id="chiefInvestigator" name="chiefInvestigator" className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500" />
                        </div>
                        <div className="mb-6">
                            <label htmlFor="agency" className="block text-sm font-medium text-gray-700">Agency/Company:</label>
                            <input type="text" id="agency" name="agency" className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500" />
                        </div>
                    </section>

                    {/* Section 2: Scientific Review */}
                    <section className="mb-8">
                        <h2 className="text-2xl font-bold mb-4">Scientific Review</h2>
                        <div className="mb-6">
                            <label htmlFor="scientificReview" className="block text-sm font-medium text-gray-700">Scientific Review:</label>
                            <p className="text-gray-500 mb-2">Respect for animals must underpin all decisions and actions involving the care and use of animals for scientific purposes. Applying high standards of scientific integrity is one of the governing principles outlined in the Australian Code for the Care and Use of Animals for Scientific Purposes - 8th Edition (the Code).</p>
                            <textarea id="scientificReview" name="scientificReview" rows={4} className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"></textarea>
                        </div>
                    </section>

                    {/* Section 3: Project Personnel */}
                    <section className="mb-8">
                        <h2 className="text-2xl font-bold mb-4">Project Personnel</h2>
                        <div className="mb-6">
                            <label htmlFor="personnelList" className="block text-sm font-medium text-gray-700">List of Personnel:</label>
                            <p className="text-gray-500 mb-2">Please identify an alternative contact person for the project and describe their experience with designated fauna and techniques.</p>
                            <textarea id="personnelList" name="personnelList" rows={4} className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"></textarea>
                        </div>
                    </section>

                    {/* Section 4: Project Details */}
                    <section className="mb-8">
                        <h2 className="text-2xl font-bold mb-4">Project Details</h2>
                        <div className="mb-6">
                            <label htmlFor="projectDescription" className="block text-sm font-medium text-gray-700">Project Description:</label>
                            <p className="text-gray-500 mb-2">Describe the project in detail, including its objectives, methodologies, and expected outcomes.</p>
                            <textarea id="projectDescription" name="projectDescription" rows={4} className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"></textarea>
                        </div>
                        <div className="mb-6">
                            <label htmlFor="speciesTable" className="block text-sm font-medium text-gray-700">Species and Number of Individuals:</label>
                            <p className="text-gray-500 mb-2">Please use current taxonomy from the NOMOS - taxonomic names management system. You may attach as a spreadsheet as long as it contains the same information.</p>
                            <table className="w-full mb-4 border-collapse border border-gray-300">
                                <thead>
                                    <tr>
                                        <th className="border border-gray-300 px-4 py-2">Scientific Name</th>
                                        <th className="border border-gray-300 px-4 py-2">Common Name</th>
                                        <th className="border border-gray-300 px-4 py-2">Total Number</th>
                                        <th className="border border-gray-300 px-4 py-2">Method of Marking/Sampling</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td className="border border-gray-300 px-4 py-2"><input type="text" className="w-full px-2 py-1 border border-gray-300 rounded-md" /></td>
                                        <td className="border border-gray-300 px-4 py-2"><input type="text" className="w-full px-2 py-1 border border-gray-300 rounded-md" /></td>
                                        <td className="border border-gray-300 px-4 py-2"><input type="number" className="w-full px-2 py-1 border border-gray-300 rounded-md" /></td>
                                        <td className="border border-gray-300 px-4 py-2"><input type="text" className="w-full px-2 py-1 border border-gray-300 rounded-md" /></td>
                                    </tr>
                                    {/* Add more rows as needed */}
                                </tbody>
                            </table>
                        </div>
                    </section>

                    <div className="text-center">
                        <button type="submit" className="px-6 py-2 bg-indigo-600 text-white font-medium rounded-md shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                            Submit
                        </button>
                    </div>
                </form>




            </main>
        </div>
    );
}
