import { NgModule }      from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { RouterModule }  from '@angular/router';
import { HttpModule }    from '@angular/http';
import { FormsModule, ReactiveFormsModule }                     from '@angular/forms';
//import { LocalStorageService, LOCAL_STORAGE_SERVICE_CONFIG }    from 'angular-2-local-storage';

import { AppComponent }             from './components/app.component';
import { HomeComponent }            from './components/home.component';
import { DashboardComponent }       from './components/dashboard.component';
import { ExecutionsInfoComponent }  from './components/executions/info.component';
import { ExecutionsListComponent }  from './components/executions/list.component';
import { ExecutionsNewComponent }   from './components/executions/new.component';
import { NavbarComponent }          from './components/navbar.component';

import { ApiService }       from './services/api.service';
import { StorageService }   from './services/storage.service';
import { ToDatePipe }       from './pipes/todate.pipe'
import { CapitalizePipe }   from './pipes/capitalize.pipe'

// Create config options (see ILocalStorageServiceConfigOptions) for deets:
let localStorageServiceConfig = {
    prefix: 'zoe',
    storageType: 'sessionStorage'
};

@NgModule({
    imports: [
        BrowserModule,
        FormsModule,
        ReactiveFormsModule,
        HttpModule,
        RouterModule.forRoot([
            { path: '',                component: HomeComponent,            pathMatch: 'full' },
            { path: 'dashboard',       component: DashboardComponent,       pathMatch: 'full' },
            { path: 'executions/list', component: ExecutionsListComponent,  pathMatch: 'full' },
            { path: 'executions/new',  component: ExecutionsNewComponent,   pathMatch: 'full' },
            { path: 'executions/:id',  component: ExecutionsInfoComponent }
        ])
    ],
    declarations: [
        CapitalizePipe,
        ToDatePipe,
        AppComponent,
        NavbarComponent,
        HomeComponent,
        DashboardComponent,
        ExecutionsListComponent,
        ExecutionsInfoComponent,
        ExecutionsNewComponent
    ],
    providers: [
        ApiService,
        StorageService,
//        LocalStorageService,
//        {
//            provide: LOCAL_STORAGE_SERVICE_CONFIG, useValue: localStorageServiceConfig
//        }
    ],
    bootstrap: [
        AppComponent
    ]
})

export class AppModule { }
