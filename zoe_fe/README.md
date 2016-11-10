# Zoe Front End

This project was generated with [angular-cli](https://github.com/angular/angular-cli) version 1.0.0-beta.16.

## Development server
Run `ng serve` for a dev server. Navigate to `http://localhost:4200/`. The app will automatically reload if you change any of the source files.

## Code scaffolding

Run `ng generate component component-name` to generate a new component. You can also use `ng generate directive/pipe/service/class`.

# Configuration

Edit file `/src/enviroments/environments.prod.ts` and configure the path of the zoe Front End application, and the url for the zoe APIs, you can use a relative path in case it is deployed on the same server.

# Installation

Run `npm install` to install all the application's dependencies.
Run `ng build --env=prod --output-path=build/prod/` to build the application in `build/prod` folder.

## Build

Run `ng build` to build the project. The build artifacts will be stored in the `dist/` directory. Use the `-prod` flag for a production build.

### Change the BaseHref

In order to change the `<base href="/">` within the `index.html file`, is it possible to add the following parameter to the `ng build` command: `--base-href x`, where x is the value of the new href. 

## Running unit tests

Run `ng test` to execute the unit tests via [Karma](https://karma-runner.github.io).

## Running end-to-end tests

Run `ng e2e` to execute the end-to-end tests via [Protractor](http://www.protractortest.org/). 
Before running the tests make sure you are serving the app via `ng serve`.

## Deploying to Github Pages

Run `ng github-pages:deploy` to deploy to Github Pages.

## Further help

To get more help on the `angular-cli` use `ng --help` or go check out the [Angular-CLI README](https://github.com/angular/angular-cli/blob/master/README.md).
