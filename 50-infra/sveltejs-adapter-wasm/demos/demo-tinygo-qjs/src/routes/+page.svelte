<script>
    export let data;
</script>

<h1>Home Page (SSR)</h1>
<p>This page is rendered on demand.</p>
<p>Current Time: {new Date().toISOString()}</p>
<a href="/about">Go to About (SSG)</a>
