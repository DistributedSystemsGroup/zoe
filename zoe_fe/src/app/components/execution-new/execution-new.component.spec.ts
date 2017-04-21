/* tslint:disable:no-unused-variable */

import { TestBed, async, ComponentFixture } from '@angular/core/testing';
import { ExecutionNewComponent } from './execution-new.component';
import { By } from '@angular/platform-browser';
import { ApiService } from '../../services/api.service';
import { FromUnixPipe, DateFormatPipe } from 'angular2-moment';
import { CapitalizePipe } from '../../pipes/capitalize.pipe';
import { APP_BASE_HREF } from '@angular/common';
import { routing, ZoeRoutingProviders }  from '../../app-routing.module';
import { Routes, RouterModule, Router } from '@angular/router';

let comp:    ExecutionNewComponent;
let fixture: ComponentFixture<ExecutionNewComponent>;

describe('Component: ExecutionNew', () => {
  let apiServiceStub = {
    startExecution: (name: string, application: Object) => 1
  };

  let routerStub = {
    navigateByUrl: (url: string) => true
  }

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [
        ExecutionNewComponent,
        CapitalizePipe,
        FromUnixPipe,
        DateFormatPipe
      ], // declare the test component
      providers: [
        {provide: Router, useValue: routerStub },
        {provide: ApiService, useValue: apiServiceStub },
        ZoeRoutingProviders,
        {provide: APP_BASE_HREF, useValue : '/' }
      ]
    });

    fixture = TestBed.createComponent(ExecutionNewComponent);

    comp = fixture.componentInstance; // BannerComponent test instance

    let apiService = TestBed.get(ApiService);
  });

  it('should create an instance', () => {
    expect(fixture).toBeTruthy();
  });

  it('should have "Name" input field', () => {
    expect(fixture.debugElement.query(By.css('label[for="inputName"]')).nativeElement.textContent).toContain('Name');
  });

  it('should have "Description" input field', () => {
    expect(fixture.debugElement.query(By.css('label[for="inputDescription"]')).nativeElement.textContent).toContain('Description');
  });

  it('should have "Submit" button', () => {
    expect(fixture.debugElement.query(By.css('button[type="submit"]')).nativeElement.textContent).toContain('Submit');
  });
});
