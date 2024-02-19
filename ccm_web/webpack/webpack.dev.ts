import webpack from 'webpack'
import { merge } from 'webpack-merge'

import commonConfig from './webpack.common.js'
console.log('webpack Dev File')

const devConfig: webpack.Configuration = merge(commonConfig, {
  mode: 'development',
  devtool: 'inline-source-map'
})

export default devConfig
