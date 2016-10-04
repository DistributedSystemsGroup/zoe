import { ModuleWithProviders }  from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

import { HomeComponent }            from './components/home.component';
import { DashboardComponent }       from './components/dashboard.component';
import { ExecutionsInfoComponent }  from './components/executions/info.component';
import { ExecutionsListComponent }  from './components/executions/list.component';
import { ExecutionsNewComponent }   from './components/executions/new.component';

const appRoutes: Routes = [
    { path: '',                component: HomeComponent,            pathMatch: 'full' },
    { path: 'dashboard',       component: DashboardComponent,       pathMatch: 'full' },
    { path: 'executions/list', component: ExecutionsListComponent,  pathMatch: 'full' },
    { path: 'executions/new',  component: ExecutionsNewComponent,   pathMatch: 'full' },
    { path: 'executions/:id',  component: ExecutionsInfoComponent }
];

export const routing: ModuleWithProviders = RouterModule.forRoot(appRoutes);