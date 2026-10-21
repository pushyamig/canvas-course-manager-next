/*
References:
- https://eslint.org/docs/latest/use/configure/configuration-files
- https://github.com/mightyiam/eslint-config-love (successor of eslint-config-standard-with-typescript)
*/

import stylistic from '@stylistic/eslint-plugin'
import { defineConfig } from 'eslint/config'
import react from 'eslint-plugin-react'
import tseslint from 'typescript-eslint'

export default defineConfig(
  { ignores: ['bundles/', 'dist/', 'node_modules/'] },
  {
    files: ['client/src/**/*.{ts,tsx}', 'webpack/**/*.ts'],
    extends: [
      react.configs.flat.recommended,
      // tsconfig uses "jsx": "react-jsx", so React doesn't need to be imported for JSX
      react.configs.flat['jsx-runtime'],
      tseslint.configs.recommendedTypeChecked
    ],
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname
      }
    },
    settings: {
      react: {
        version: 'detect'
      }
    },
    plugins: {
      '@stylistic': stylistic
    },
    rules: {
      'no-void': ['error', { allowAsStatement: true }],
      '@typescript-eslint/no-floating-promises': ['error', { ignoreVoid: true }],
      // Style rules matching eslint-config-standard-with-typescript on main
      '@stylistic/semi': ['error', 'never'],
      '@stylistic/quotes': ['error', 'single', { avoidEscape: true }],
      // JSX indentation is ignored, as in standard-with-typescript
      '@stylistic/indent': ['error', 2, {
        SwitchCase: 1,
        ignoredNodes: ['JSXElement', 'JSXElement > *', 'JSXAttribute', 'JSXIdentifier', 'JSXNamespacedName', 'JSXMemberExpression', 'JSXSpreadAttribute', 'JSXExpressionContainer', 'JSXOpeningElement', 'JSXClosingElement', 'JSXFragment', 'JSXOpeningFragment', 'JSXClosingFragment', 'JSXText', 'JSXEmptyExpression', 'JSXSpreadChild']
      }],
      '@stylistic/space-infix-ops': 'error',
      '@stylistic/keyword-spacing': 'error',
      '@stylistic/object-curly-spacing': ['error', 'always']
    }
  }
)
