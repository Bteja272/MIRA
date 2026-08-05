import {
  useEffect,
  useState,
} from "react";

export function NetworkStatusBanner() {
  const [
    isOnline,
    setIsOnline,
  ] = useState(
    navigator.onLine,
  );

  useEffect(() => {
    function handleOnline(): void {
      setIsOnline(true);
    }

    function handleOffline(): void {
      setIsOnline(false);
    }

    window.addEventListener(
      "online",
      handleOnline,
    );

    window.addEventListener(
      "offline",
      handleOffline,
    );

    return () => {
      window.removeEventListener(
        "online",
        handleOnline,
      );

      window.removeEventListener(
        "offline",
        handleOffline,
      );
    };
  }, []);

  if (isOnline) {
    return null;
  }

  return (
    <div
      className="network-status-banner"
      role="alert"
      aria-live="assertive"
    >
      Your device appears to be offline. Existing
      page content remains visible, but API requests
      will fail until connectivity returns.
    </div>
  );
}