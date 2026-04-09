-- Sugar LSP configuration for Neovim
-- Add this to your init.lua or source this file

vim.filetype.add({ extension = { sugar = "sugar" } })

local lspconfig = require("lspconfig")
local configs = require("lspconfig.configs")

if not configs.sugar then
  configs.sugar = {
    default_config = {
      cmd = { "abstra-sugar", "lsp" },
      filetypes = { "sugar" },
      root_dir = lspconfig.util.find_git_ancestor,
      settings = {},
    },
  }
end

lspconfig.sugar.setup({})
