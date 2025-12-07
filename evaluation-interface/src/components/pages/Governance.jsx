const Governance = () => (
  <div className="space-y-6">
    <h1 className="text-3xl font-bold">Governance & Version Log</h1>
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Model Version History</h3>
      <div className="space-y-3">
        {['v2.3.1', 'v2.3.0', 'v2.2.5', 'v2.2.4'].map((version, i) => (
          <div key={version} className="border-l-4 border-blue-500 pl-4 py-2">
            <div className="flex justify-between items-center">
              <div>
                <span className="font-medium">{version}</span>
                <p className="text-sm text-gray-600">Deployed on 2024-{12 - i}-{String(15 - i * 3).padStart(2, '0')}</p>
              </div>
              <span className={`text-xs px-2 py-1 rounded ${i === 0 ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                {i === 0 ? 'Current' : 'Previous'}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  </div>
);

export default Governance;