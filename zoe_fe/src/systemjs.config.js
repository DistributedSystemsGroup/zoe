/**
 * System configuration for Angular 2 samples
 * Adjust as necessary for your application needs.
 */
(function (global) {
  System.config({
    paths: {
      // paths serve as alias
      'npm:': 'node_modules/'
    },
    // map tells the System loader where to look for things
    map: {
      // our app is within the app folder
      app:                                    'dist',
      // angular bundles
      '@angular/core':                        'npm:@angular/core/bundles/core.umd.js',
      '@angular/common':                      'npm:@angular/common/bundles/common.umd.js',
      '@angular/compiler':                    'npm:@angular/compiler/bundles/compiler.umd.js',
      '@angular/platform-browser':            'npm:@angular/platform-browser/bundles/platform-browser.umd.js',
      '@angular/platform-browser-dynamic':    'npm:@angular/platform-browser-dynamic/bundles/platform-browser-dynamic.umd.js',
      '@angular/http':                        'npm:@angular/http/bundles/http.umd.js',
      '@angular/router':                      'npm:@angular/router/bundles/router.umd.js',
      '@angular/forms':                       'npm:@angular/forms/bundles/forms.umd.js',
      // other libraries
      'rxjs':                                 'npm:rxjs',
      'angular2-in-memory-web-api':           'npm:angular2-in-memory-web-api',
      'moment':                               'npm:moment/moment.js',
      '@ng-bootstrap/ng-bootstrap':           'npm:@ng-bootstrap/ng-bootstrap'
    },
    // packages tells the System loader how to load when no filename and/or no extension
    packages: {
      app: {
        main: './main.js',
        defaultExtension: 'js'
      },
      rxjs: {
        defaultExtension: 'js'
      },
      'angular2-in-memory-web-api': {
        main: './index.js',
        defaultExtension: 'js'
      },
      '@ng-bootstrap/ng-bootstrap': {
        defaultExtension: 'js',
        main: 'index.js'
      },
      '@ng-bootstrap/ng-bootstrap/accordion': {
        defaultExtension: 'js',
        main: 'index.js'
      },
      '@ng-bootstrap/ng-bootstrap/alert': {
        defaultExtension: 'js',
        main: 'index.js'
      },
      '@ng-bootstrap/ng-bootstrap/buttons': {
        defaultExtension: 'js',
        main: 'index.js'
      },
      '@ng-bootstrap/ng-bootstrap/carousel': {
        defaultExtension: 'js',
        main: 'index.js'
      },
      '@ng-bootstrap/ng-bootstrap/collapse': {
        defaultExtension: 'js',
        main: 'index.js'
      },
      '@ng-bootstrap/ng-bootstrap/dropdown': {
        defaultExtension: 'js',
        main: 'index.js'
      },
      '@ng-bootstrap/ng-bootstrap/pagination': {
        defaultExtension: 'js',
        main: 'index.js'
      },
      '@ng-bootstrap/ng-bootstrap/popover': {
        defaultExtension: 'js',
        main: 'index.js'
      },
      '@ng-bootstrap/ng-bootstrap/progressbar': {
        defaultExtension: 'js',
        main: 'index.js'
      },
      '@ng-bootstrap/ng-bootstrap/rating': {
        defaultExtension: 'js',
        main: 'index.js'
      },
      '@ng-bootstrap/ng-bootstrap/tabset': {
        defaultExtension: 'js',
        main: 'index.js'
      },
      '@ng-bootstrap/ng-bootstrap/timepicker': {
        defaultExtension: 'js',
        main: 'index.js'
      },
      '@ng-bootstrap/ng-bootstrap/tooltip': {
        defaultExtension: 'js',
        main: 'index.js'
      },
      '@ng-bootstrap/ng-bootstrap/typeahead': {
        defaultExtension: 'js',
        main: 'index.js'
      }
    }
  });
})(this);
