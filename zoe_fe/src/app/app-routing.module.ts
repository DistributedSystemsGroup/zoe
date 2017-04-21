import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

import { LoginComponent } from './components/login/login.component';
import { ExecutionInfoComponent } from './components/execution-info/execution-info.component';
import { ExecutionNewComponent } from './components/execution-new/execution-new.component';
import { ExecutionListComponent } from './components/execution-list/execution-list.component';






import { ModuleWithProviders } from '@angular/core';

const appRoutes: Routes = [
  { path: '',                component: LoginComponent,          pathMatch: 'full' },
  { path: 'executions/list', component: ExecutionListComponent,  pathMatch: 'full' },
  { path: 'executions/new',  component: ExecutionNewComponent,   pathMatch: 'full' },
  { path: 'executions/:id',  component: ExecutionInfoComponent }
];

export const ZoeRoutingProviders: any[] = [

];

export const routing: ModuleWithProviders = RouterModule.forRoot(appRoutes);

/*
const routes: Routes = [
  { path: '',                component: LoginComponent,          pathMatch: 'full' },
  { path: 'executions/list', component: ExecutionListComponent,  pathMatch: 'full' },
  { path: 'executions/new',  component: ExecutionNewComponent,   pathMatch: 'full' },
  { path: 'executions/:id',  component: ExecutionInfoComponent }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule],
  providers: []
})
export class ZoeRoutingModule { }
*/
