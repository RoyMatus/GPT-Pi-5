import { build } from "esbuild";
await build({
    entryPoints: ["frontend/app.jsx"],
    bundle: true,
    minify: true,
    outfile: "src/gpt_pi/web/assets/app.js",
    format: "esm",
    target: ["chrome120"],
    define: { "process.env.NODE_ENV": '"production"' },
    legalComments: "linked",
    jsx: "automatic",
    sourcemap: false,
});
