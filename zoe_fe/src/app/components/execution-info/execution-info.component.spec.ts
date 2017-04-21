/* tslint:disable:no-unused-variable */

import { TestBed, async, ComponentFixture } from '@angular/core/testing';
import { Execution }  from '../../entities/execution'
import { Service } from '../../entities/service'
import { By } from '@angular/platform-browser';
import { ExecutionInfoComponent } from './execution-info.component';
import { ApiService } from '../../services/api.service';
import { FromUnixPipe, DateFormatPipe } from 'angular2-moment';
import { CapitalizePipe } from '../../pipes/capitalize.pipe';
import { ActivatedRoute } from '@angular/router';

let comp:    ExecutionInfoComponent;
let fixture: ComponentFixture<ExecutionInfoComponent>;
let spyGetExecutionDetails;
let spyGetServiceDetails;

describe('Component: ExecutionInfo', () => {
  let executionDetails = {
    'id': '123',
    'name': 'Execution Test',
    'owner': 'owner1234',
    'status': 'running',
    'services': [456]
  };
  let execution = new Execution().deserialize(executionDetails);

  let serviceDetails = {
    'id': '456',
    'name': 'Service Test'
  };

  let service = new Service().deserialize(serviceDetails);

  let activateRouteStub = {
    params: [{"id":100}]
  };

  let apiServiceStub = {
    getExecutionDetails: (id: string) => execution,
    getServiceDetails: (id: string) => service
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [
        ExecutionInfoComponent,
        CapitalizePipe,
        FromUnixPipe,
        DateFormatPipe
      ], // declare the test component
      providers: [
        {provide: ActivatedRoute, useValue: activateRouteStub },
        {provide: ApiService, useValue: apiServiceStub }
      ]
    });

    fixture = TestBed.createComponent(ExecutionInfoComponent);

    comp = fixture.componentInstance; // BannerComponent test instance

    let apiService = TestBed.get(ApiService);

    spyGetExecutionDetails = spyOn(apiService, 'getExecutionDetails')
        .and.returnValue(Promise.resolve(execution));

    spyGetServiceDetails = spyOn(apiService, 'getServiceDetails')
        .and.returnValue(Promise.resolve(service));
  });

  it('should create an instance', () => {
    expect(fixture).toBeTruthy();
  });

  it('should not show "Details" before "getExecutionDetails" call', () => {
    expect(fixture.debugElement.query(By.css('#execution-details'))).toBeNull();
    expect(fixture.debugElement.query(By.css('#execution-service'))).toBeNull();

    expect(spyGetExecutionDetails.calls.any()).toBe(false, 'getExecutionDetails not yet called');
    expect(spyGetServiceDetails.calls.any()).toBe(false, 'getServiceDetails not yet called');
  });

  it('should still not show quote after component initialized', () => {
    fixture.detectChanges();

    expect(fixture.debugElement.query(By.css('.spinner-title')).nativeElement.textContent).toContain('Loading...');
    expect(spyGetExecutionDetails.calls.any()).toBe(true, 'getExecutionDetails called');
    expect(spyGetServiceDetails.calls.any()).toBe(false, 'getServiceDetails called');
  });

  it('should show execution details and service', async(() => {
    fixture.detectChanges();

    fixture.whenStable().then(() => { // wait for async getQuote
      fixture.detectChanges();        // update view with quote
      expect(fixture.debugElement.query(By.css('#execution-details')).nativeElement).toBeDefined();
      expect(fixture.debugElement.query(By.css('#execution-service')).nativeElement).toBeDefined();
    });
  }));
});