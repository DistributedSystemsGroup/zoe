import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { HttpModule, BaseRequestOptions, RequestOptions, Headers } from '@angular/http';
import { FromUnixPipe, DateFormatPipe } from 'angular2-moment';
import { routing, ZoeRoutingProviders }  from './app-routing.module';

import { AppComponent } from './app.component';
import { CapitalizePipe } from './pipes/capitalize.pipe';
import { LoginComponent } from './components/login/login.component';
import { NavbarComponent } from './components/navbar/navbar.component';
import { ExecutionInfoComponent } from './components/execution-info/execution-info.component';
import { ExecutionNewComponent } from './components/execution-new/execution-new.component';
import { ExecutionListComponent } from './components/execution-list/execution-list.component';

import { ApiService }       from './services/api.service';
import { StorageService }   from './services/storage.service';

import { environment } from '../environments/environment'

/** When FE and BE are deployed on 2 different hostname we need to
 * enable CORS on the BE. In order to let the browser support the 
 * cookies between each HTTP request, we need to set 2 different 
 * options by default in the whole application.
**/
class CORSRequestOptions extends BaseRequestOptions {
  headers: Headers = new Headers({
    'X-Requested-With': 'XMLHttpRequest'
  });
  withCredentials: boolean = true;
}

let providers: any[] = [
  ApiService,
  StorageService,
  ZoeRoutingProviders
];

if (environment.cors) {
  providers.push({ provide: RequestOptions, useClass: CORSRequestOptions })
}

@NgModule({
  declarations: [
    AppComponent,
    CapitalizePipe,
    FromUnixPipe,
    DateFormatPipe,
    LoginComponent,
    NavbarComponent,
    ExecutionInfoComponent,
    ExecutionNewComponent,
    ExecutionListComponent
  ],
  imports: [
    BrowserModule,
    FormsModule,
    ReactiveFormsModule,
    HttpModule,
    routing
  ],
  providers: providers,
  bootstrap: [
    AppComponent
  ]
})
export class AppModule { }
