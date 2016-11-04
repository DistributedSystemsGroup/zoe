/* tslint:disable:no-unused-variable */
import { TestBed, async } from '@angular/core/testing';
import { AppComponent } from './app.component';

describe('App', () => {

    beforeEach(function() {
        this.app = new AppComponent();
    });

    it('should create the app', function() {
        expect(this.app).toBeTruthy();
    });
});

/*
import { TestBed, async } from '@angular/core/testing';
import { AppComponent } from './app.component';

import { FromUnixPipe, DateFormatPipe } from 'angular2-moment';
import { CapitalizePipe } from './pipes/capitalize.pipe';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { HttpModule } from '@angular/http';
import { APP_BASE_HREF } from '@angular/common';
import { routing, ZoeRoutingProviders }  from './app-routing.module';

import { NavbarComponent } from './components/navbar/navbar.component';
import { LoginComponent } from './components/login/login.component';
import { ExecutionInfoComponent } from './components/execution-info/execution-info.component';
import { ExecutionNewComponent } from './components/execution-new/execution-new.component';
import { ExecutionListComponent } from './components/execution-list/execution-list.component';

import { ApiService }       from './services/api.service';
import { StorageService }   from './services/storage.service';
import { ActivatedRoute } from '@angular/router';

let fixture;

describe('App: Zoe', () => {
  let apiServiceStub = {
    getAllExecutions: () => executions
  };

  let storageServiceStub = {
    getUsername: () => "admin"
  };

  let activateRouteStub = {
    params: [{"id":100}]
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [
        AppComponent,
        LoginComponent,
        NavbarComponent,
        ExecutionInfoComponent,
        ExecutionNewComponent,
        ExecutionListComponent,
        CapitalizePipe,
        FromUnixPipe,
        DateFormatPipe
      ],
      imports: [
        FormsModule,
        ReactiveFormsModule,
        HttpModule,
        routing
      ],
      providers: [
        {provide: ActivatedRoute, useValue: activateRouteStub },
        {provide: ApiService, useValue: apiServiceStub },
        {provide: StorageService, useValue: storageServiceStub },
        ApiService,
        StorageService,
        ZoeRoutingProviders,
        {provide: APP_BASE_HREF, useValue : '/' }
      ],
      bootstrap: [
        AppComponent
      ]
    });

    fixture = TestBed.createComponent(AppComponent);
  });

  it('should create the app', async(() => {
    let app = fixture.debugElement.componentInstance;
    expect(app).toBeTruthy();
  }));

  it(`should have as title 'Zoe - Dashboard'`, async(() => {
    let app = fixture.debugElement.componentInstance;
    expect(app.title).toEqual('Zoe - Dashboard');
  }));

  it('should render the navbar', async(() => {
    fixture.detectChanges();
    let compiled = fixture.debugElement.nativeElement;
    expect(compiled.querySelector('nav a.navbar-brand').textContent).toContain('Zoe');
  }));

  it('should render the login form', async(() => {
    let fixture = TestBed.createComponent(AppComponent);
    fixture.detectChanges();
    let compiled = fixture.debugElement.nativeElement;
    expect(compiled.querySelector('h1').textContent).toContain('Login');
  }));
});
*/