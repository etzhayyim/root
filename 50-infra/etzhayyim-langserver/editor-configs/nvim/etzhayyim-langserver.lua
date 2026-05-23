-- etzhayyim-langserver/editor-configs/nvim/etzhayyim-langserver.lua
--
-- Neovim plugin module for attaching to fleet-hosted LSPs (Layer 8).
--
-- Usage in your nvim config:
--   local fleet = require("etzhayyim-langserver")
--   fleet.setup({
--     -- Optional: pin to a specific etzhayyim/root checkout where lsp-fleet.json lives.
--     -- Defaults to scanning $ETZHAYYIM_REPO then ~/github/etzhayyim/root.
--     registry_path = vim.fn.expand("~/github/etzhayyim/root/50-infra/etzhayyim-langserver/scripts/lsp-fleet.json"),
--     -- Optional: per-language overrides
--     languages = { rust = { root_markers = { "Cargo.toml" } } },
--   })
--
-- Then open a Rust file — fleet LSP attaches automatically.

local M = {}

local DEFAULT_REGISTRY_PATHS = {
  vim.fn.expand("$ETZHAYYIM_REPO/50-infra/etzhayyim-langserver/scripts/lsp-fleet.json"),
  vim.fn.expand("~/github/etzhayyim/root/50-infra/etzhayyim-langserver/scripts/lsp-fleet.json"),
}

local LANG_TO_FILETYPES = {
  rust = { "rust" },
  python = { "python" },
  typescript = { "typescript", "typescriptreact", "javascript", "javascriptreact" },
  go = { "go", "gomod" },
  lua = { "lua" },
  ruby = { "ruby" },
}

local DEFAULT_ROOT_MARKERS = {
  rust = { "Cargo.toml" },
  python = { "pyproject.toml", "setup.py", "setup.cfg" },
  typescript = { "tsconfig.json", "package.json" },
  go = { "go.mod" },
  lua = { ".luarc.json", ".luarc.jsonc" },
  ruby = { "Gemfile", ".ruby-version" },
}

local function load_registry(path)
  local fd = io.open(path, "r")
  if not fd then return nil end
  local body = fd:read("*a")
  fd:close()
  local ok, json = pcall(vim.json.decode, body)
  if not ok then return nil end
  return json
end

local function find_registry(user_path)
  if user_path and vim.fn.filereadable(user_path) == 1 then
    return user_path
  end
  for _, p in ipairs(DEFAULT_REGISTRY_PATHS) do
    if vim.fn.filereadable(p) == 1 then return p end
  end
  return nil
end

function M.setup(opts)
  opts = opts or {}
  local registry_path = find_registry(opts.registry_path)
  if not registry_path then
    vim.notify("[etzhayyim-langserver] lsp-fleet.json not found; run generate-fleet-registry.sh", vim.log.levels.WARN)
    return
  end
  local registry = load_registry(registry_path)
  if not registry or not registry.entries then
    vim.notify("[etzhayyim-langserver] failed to parse " .. registry_path, vim.log.levels.ERROR)
    return
  end

  for _, entry in ipairs(registry.entries) do
    local lang = entry.lang
    local filetypes = LANG_TO_FILETYPES[lang]
    if filetypes then
      local user_lang = (opts.languages or {})[lang] or {}
      local root_markers = user_lang.root_markers or DEFAULT_ROOT_MARKERS[lang] or {}

      vim.api.nvim_create_autocmd("FileType", {
        pattern = filetypes,
        callback = function(args)
          local bufname = vim.api.nvim_buf_get_name(args.buf)
          local root_dir = vim.fs.dirname(vim.fs.find(root_markers, {
            path = bufname,
            upward = true,
          })[1]) or vim.fn.getcwd()

          vim.lsp.start({
            name = "etzhayyim-" .. lang,
            cmd = vim.lsp.rpc.connect(entry.mesh_ip, entry.port),
            root_dir = root_dir,
            -- Pass through workspace folders so the fleet LSP indexes from
            -- the editor's view. The fleet LSP runs on the remote workspace
            -- it was launched with; this rootDir hint is informational on
            -- editor-side only.
          })
        end,
      })
    end
  end

  vim.api.nvim_create_user_command("EtzhayyimLangserverStatus", function()
    print(vim.inspect(registry))
  end, {})
end

return M
