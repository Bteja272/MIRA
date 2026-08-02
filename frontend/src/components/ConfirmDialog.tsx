import {
  useEffect,
  useRef,
} from "react";

interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  description: string;
  confirmLabel: string;
  isConfirming?: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}

export function ConfirmDialog({
  isOpen,
  title,
  description,
  confirmLabel,
  isConfirming = false,
  onCancel,
  onConfirm,
}: ConfirmDialogProps) {
  const dialogRef =
    useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;

    if (!dialog) {
      return;
    }

    if (
      isOpen &&
      !dialog.open
    ) {
      dialog.showModal();
    }

    if (
      !isOpen &&
      dialog.open
    ) {
      dialog.close();
    }
  }, [isOpen]);

  useEffect(() => {
    const dialog = dialogRef.current;

    if (!dialog) {
      return;
    }

    function handleCancel(
      event: Event,
    ): void {
      event.preventDefault();

      if (!isConfirming) {
        onCancel();
      }
    }

    dialog.addEventListener(
      "cancel",
      handleCancel,
    );

    return () => {
      dialog.removeEventListener(
        "cancel",
        handleCancel,
      );
    };
  }, [
    isConfirming,
    onCancel,
  ]);

  return (
    <dialog
      className="confirm-dialog"
      ref={dialogRef}
      aria-labelledby="confirm-dialog-title"
      aria-describedby="confirm-dialog-description"
    >
      <div className="confirm-dialog__content">
        <p className="eyebrow">
          Permanent action
        </p>

        <h2 id="confirm-dialog-title">
          {title}
        </h2>

        <p id="confirm-dialog-description">
          {description}
        </p>

        <div className="confirm-dialog__actions">
          <button
            className="button button--secondary"
            type="button"
            disabled={isConfirming}
            onClick={onCancel}
          >
            Cancel
          </button>

          <button
            className="button button--danger"
            type="button"
            disabled={isConfirming}
            onClick={onConfirm}
          >
            {isConfirming
              ? "Deleting…"
              : confirmLabel}
          </button>
        </div>
      </div>
    </dialog>
  );
}