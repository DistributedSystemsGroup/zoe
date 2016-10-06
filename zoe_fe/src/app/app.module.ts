import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { HttpModule } from '@angular/http';
import { routing, ZoeRoutingProviders }  from './app-routing.module';

import { AppComponent } from './app.component';
import { CapitalizePipe } from './pipes/capitalize.pipe';
import { ToDatePipe } from './pipes/to-date.pipe';
import { LoginComponent } from './components/login/login.component';
import { NavbarComponent } from './components/navbar/navbar.component';
import { ExecutionInfoComponent } from './components/execution-info/execution-info.component';
import { ExecutionNewComponent } from './components/execution-new/execution-new.component';
import { ExecutionListComponent } from './components/execution-list/execution-list.component';

import { ApiService }       from './services/api.service';
import { StorageService }   from './services/storage.service';

@NgModule({
  declarations: [
    AppComponent,
    CapitalizePipe,
    ToDatePipe,
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
  providers: [
    ApiService,
    StorageService,
    ZoeRoutingProviders
  ],
  bootstrap: [
    AppComponent
  ]
})
export class AppModule { }
