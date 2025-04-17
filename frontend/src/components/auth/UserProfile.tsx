import { useState } from 'react';
import { useAuth } from '../../context/useAuth';

export default function UserProfile() {
  const { user, signOut } = useAuth();
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const handleSignOut = async () => {
    setLoading(true);
    setErrorMessage('');
    try {
      await signOut();
    } catch (err) {
      if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage('Failed to sign out. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return <div>Not logged in</div>;
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex items-center space-x-4 mb-6">
        <div className="h-12 w-12 rounded-full bg-blue-100 flex items-center justify-center">
          <span className="text-blue-800 font-bold text-xl">
            {user.email.charAt(0).toUpperCase()}
          </span>
        </div>
        <div>
          <h2 className="text-xl font-medium text-gray-900">{user.email}</h2>
          <p className="text-sm text-gray-500">User ID: {user.id}</p>
        </div>
      </div>

      <div className="border-t border-gray-200 pt-4">
        <h3 className="text-lg font-medium mb-3">Account Settings</h3>
        <div className="space-y-3">
          <p className="text-gray-700">
            <span className="font-medium">Email: </span>
            {user.email}
          </p>
          <p className="text-gray-700">
            <span className="font-medium">Role: </span>
            {user.role || 'Standard User'}
          </p>
        </div>
      </div>

      {errorMessage && (
        <div className="mt-4 text-sm text-red-600">{errorMessage}</div>
      )}

      <div className="mt-6">
        <button
          onClick={handleSignOut}
          disabled={loading}
          className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
        >
          {loading ? 'Signing out...' : 'Sign out'}
        </button>
      </div>
    </div>
  );
}