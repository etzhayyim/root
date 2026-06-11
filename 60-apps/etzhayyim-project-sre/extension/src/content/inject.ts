window.addEventListener('message', async (event) => {
  if (event.data?.type !== 'GET_CLERK_TOKEN') return;
  try {
    const clerk = (window as any).Clerk;
    if (clerk?.session) {
      const token = await clerk.session.getToken();
      window.postMessage({ type: 'CLERK_TOKEN', token }, '*');
    }
  } catch {
    window.postMessage({ type: 'CLERK_TOKEN', token: null }, '*');
  }
});
