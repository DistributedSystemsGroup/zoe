import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { HttpModule } from '@angular/http';
import { FromUnixPipe } from 'angular2-moment';
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

import { APP_BASE_HREF } from '@angular/common';
import { environment } from '../environments/environment';

@NgModule({
  declarations: [
    AppComponent,
    CapitalizePipe,
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
    FromUnixPipe,
    routing
  ],
  providers: [
    ApiService,
    StorageService,
    ZoeRoutingProviders,
    {provide: APP_BASE_HREF, useValue : environment.baseHref }
  ],
  bootstrap: [
    AppComponent
  ]
})
export class AppModule { }
