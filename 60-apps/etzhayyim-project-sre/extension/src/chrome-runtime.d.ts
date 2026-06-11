declare namespace chrome {
  namespace runtime {
    interface MessageSender {}

    function getURL(path: string): string;

    const onInstalled: {
      addListener(listener: () => void): void;
    };

    const onMessage: {
      addListener(
        listener: (
          message: { type?: string },
          sender: MessageSender,
          sendResponse: (response?: unknown) => void
        ) => boolean | void
      ): void;
    };
  }
}
