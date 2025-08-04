export default function TestToolbarPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="text-center p-8 bg-white rounded-lg shadow-lg">
        <h1 className="text-3xl font-bold mb-4">Toolbar Test Page</h1>
        <p className="text-gray-600 mb-4">
          The @21st-extension/toolbar should be initialized in development mode.
        </p>
        <p className="text-sm text-gray-500">
          Check the browser console for initialization logs.
        </p>
      </div>
    </div>
  );
}