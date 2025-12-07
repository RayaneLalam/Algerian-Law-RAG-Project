
const ModelComparison = () => (
  <div className="space-y-6">
    <h1 className="text-3xl font-bold">Model Comparison (A vs B)</h1>
    <div className="grid grid-cols-2 gap-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Model A</h3>
        <div className="space-y-2 text-sm">
          <p><strong>Accuracy:</strong> 87.3%</p>
          <p><strong>Latency:</strong> 245ms</p>
          <p><strong>Citation Quality:</strong> 8.1/10</p>
        </div>
      </div>
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Model B</h3>
        <div className="space-y-2 text-sm">
          <p><strong>Accuracy:</strong> 89.1%</p>
          <p><strong>Latency:</strong> 312ms</p>
          <p><strong>Citation Quality:</strong> 7.8/10</p>
        </div>
      </div>
    </div>
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Head-to-Head Comparison</h3>
      <p className="text-sm text-gray-600">Run side-by-side tests and analyze model performance differences.</p>
    </div>
  </div>
);

export default ModelComparison;