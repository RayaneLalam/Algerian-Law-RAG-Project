

const DatasetBuilder = ({ savedDatasets }) => (
  <div className="space-y-6">
    <h1 className="text-3xl font-bold">Dataset Builder</h1>
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Saved Reference Answers ({savedDatasets.length})</h3>
      <div className="space-y-3">
        {savedDatasets.length === 0 ? (
          <p className="text-sm text-gray-500">No saved datasets yet. Create reference answers in the Evaluation Playground.</p>
        ) : (
          savedDatasets.map(dataset => (
            <div key={dataset.id} className="border rounded-lg p-4 bg-gray-50">
              <div className="flex justify-between items-start mb-2">
                <span className="font-medium text-sm">{dataset.query}</span>
                <span className="text-xs text-gray-500">{new Date(dataset.timestamp).toLocaleDateString()}</span>
              </div>
              <p className="text-sm text-gray-700 mb-2">{dataset.referenceAnswer}</p>
              <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">
                Top: {dataset.topCandidate.modelId}
              </span>
            </div>
          ))
        )}
      </div>
      <div className="mt-4 flex gap-2">
        <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm">
          Export Dataset
        </button>
        <button className="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300 text-sm">
          Import Dataset
        </button>
      </div>
    </div>
  </div>
);

export default DatasetBuilder;