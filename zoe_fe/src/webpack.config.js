var webpack = require('webpack');
var path = require('path');

module.exports = {
  devtool: 'inline-source-map',
  entry: [
    'webpack-dev-server/client?http://127.0.0.1:8080/',
    'webpack/hot/only-dev-server',
    './app'
  ],
  output: {
    path: path.join(__dirname, 'build'),
    filename:'bundle.js'
  },
  resolve: {
    modulesDirectories: ['node_modules', 'app'],
    extensions: ['','.js']
  },
  module:{
    loaders: [
      {
        test:/\.jsx?$/,
        exclude:/node_modules/,
        loaders:[
          'react-hot','babel?presets[]=react,presets[]=es2015'
        ]
      }
    ]
  },
  plugins: [
    new webpack.HotModuleReplacementPlugin(),
    new webpack.NoErrorsPlugin(),
    new webpack.optimize.UglifyJsPlugin()
  ]

};
