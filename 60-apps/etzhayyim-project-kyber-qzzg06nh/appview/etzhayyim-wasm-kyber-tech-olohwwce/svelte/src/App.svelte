<script lang="ts">
  const title = 'Kyber Tech'
</script>

<main>
  <h1>{title}</h1>
  <p>UI entry scaffold for kyber tech component.</p>
</main>

<style>
  :global(body) {
    margin: 0;
    font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
    background: #f8fafc;
    color: #0f172a;
  }

  main {
    min-height: 100vh;
    display: grid;
    place-content: center;
    gap: 0.75rem;
    text-align: center;
    padding: 2rem;
  }

  h1 {
    margin: 0;
    font-size: 1.8rem;
  }

  p {
    margin: 0;
    color: #334155;
  }
</style>
