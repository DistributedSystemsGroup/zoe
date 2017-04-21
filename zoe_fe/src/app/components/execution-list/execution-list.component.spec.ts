/* tslint:disable:no-unused-variable */

import { TestBed, async, ComponentFixture } from '@angular/core/testing';
import { Execution }  from '../../entities/execution';
import { Credentials }  from '../../entities/credentials';
import { StorageService } from '../../services/storage.service';
import { ApiService } from '../../services/api.service';
import { By } from '@angular/platform-browser';
import { ExecutionListComponent } from './execution-list.component';
import { LoginComponent } from '../login/login.component';
import { FromUnixPipe, DateFormatPipe } from 'angular2-moment';
import { CapitalizePipe } from '../../pipes/capitalize.pipe';
import { Router } from '@angular/router';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { RouterLinkStubDirective } from '../../testing/router-stubs';

let comp:    ExecutionListComponent;
let fixture: ComponentFixture<ExecutionListComponent>;
let spyGetAllExecutions;

describe('Component: ExecutionList', () => {
    let executions = [
        new Execution().deserialize(
            {
                'id': '1',
                'name': 'Execution Test',
                'owner': 'admin',
                'status': 'running',
                'services': [1]
            }
        ),
        new Execution().deserialize(
            {
                'id': '2',
                'name': 'Execution Test',
                'owner': 'admin',
                'status': 'running',
                'services': [2]
            }
        ),
        new Execution().deserialize(
            {
                'id': '3',
                'name': 'Execution Test',
                'owner': 'admin',
                'status': 'running',
                'services': [3]
            }
        ),
    ];

    let routerStub = {
      navigateByUrl: (url: string) => true
    };

    let apiServiceStub = {
      getAllExecutions: () => executions,
      isUserLoggedIn: () => true
    };

    let storageServiceStub = {
      getUsername: () => "admin",
      getCredentials: () => new Credentials().deserialize({
        'uid': 'admin',
        'role': 'admin'
      })
    };

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                RouterLinkStubDirective,
                ExecutionListComponent,
                LoginComponent,
                CapitalizePipe,
                FromUnixPipe,
                DateFormatPipe
            ],
            imports: [
                FormsModule,
                ReactiveFormsModule
            ],
            providers: [
                {provide: Router, useValue: routerStub },
                {provide: ApiService, useValue: apiServiceStub },
                {provide: StorageService, useValue: storageServiceStub }
            ]
        });

        fixture = TestBed.createComponent(ExecutionListComponent);

        comp = fixture.componentInstance; // BannerComponent test instance

        let apiService = TestBed.get(ApiService);

        spyGetAllExecutions = spyOn(apiService, 'getAllExecutions')
            .and.returnValue(Promise.resolve(executions));
    });

  it('should create an instance', () => {
    expect(fixture).toBeTruthy();
  });

  it('should not show the table before "getAllExecutions" call', () => {
    expect(fixture.debugElement.query(By.css('#executions-list-table'))).toBeNull();

    expect(spyGetAllExecutions.calls.any()).toBe(false, 'getAllExecutions not yet called');
  });

  it('should still not show quote after component initialized', () => {
    fixture.detectChanges();

    expect(fixture.debugElement.query(By.css('.spinner-title')).nativeElement.textContent).toContain('Loading...');
    expect(spyGetAllExecutions.calls.any()).toBe(true, 'getAllExecutions called');
  });

  it('should show execution list table', async(() => {
    fixture.detectChanges();

    fixture.whenStable().then(() => { // wait for async getQuote
      fixture.detectChanges();        // update view with quote
      expect(fixture.debugElement.query(By.css('#executions-list-table')).nativeElement).toBeDefined();
    });
  }));
});