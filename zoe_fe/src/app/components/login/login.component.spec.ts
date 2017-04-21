/* tslint:disable:no-unused-variable */

import { TestBed, async, ComponentFixture } from '@angular/core/testing';
import { LoginComponent } from './login.component';
import { By } from '@angular/platform-browser';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { FromUnixPipe, DateFormatPipe } from 'angular2-moment';
import { CapitalizePipe } from '../../pipes/capitalize.pipe';
import { Router } from '@angular/router';
import { RouterLinkStubDirective } from '../../testing/router-stubs';

let comp:    LoginComponent;
let fixture: ComponentFixture<LoginComponent>;
//let de:      DebugElement;
//let el:      HTMLElement;

describe('Component: Login', () => {
    let routerStub = {
        navigateByUrl: (url: string) => true
    };

  let apiServiceStub = {
    isUserLoggedIn: () => false,
    isLoginNeeded: () => true,
    login: (username: string, password: string) => true
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [
          RouterLinkStubDirective,
        LoginComponent,
        CapitalizePipe,
        FromUnixPipe,
        DateFormatPipe
      ], // declare the test component
      imports: [
        FormsModule,
        ReactiveFormsModule
      ],
      providers: [
        {provide: Router, useValue: routerStub },
        {provide: ApiService, useValue: apiServiceStub }
      ]
    });

    fixture = TestBed.createComponent(LoginComponent);

    comp = fixture.componentInstance; // BannerComponent test instance
  });

  it('should create an instance', () => {
    expect(fixture).toBeTruthy();
  });

  it('should have title "Login"', () => {
    fixture.whenStable().then(() => { // wait for async getQuote
      fixture.detectChanges();        // update view with quote
      expect(fixture.debugElement.query(By.css('h1')).nativeElement.textContent).toContain('Login');
    });
  });

  it('should have "Username" input field', () => {
    fixture.whenStable().then(() => { // wait for async getQuote
      fixture.detectChanges();        // update view with quote
      expect(fixture.debugElement.query(By.css('label[for="inputUsername"]')).nativeElement.textContent).toContain('Username');
    });
  });

  it('should have "Password" input field', () => {
    fixture.whenStable().then(() => { // wait for async getQuote
      fixture.detectChanges();        // update view with quote
      expect(fixture.debugElement.query(By.css('label[for="inputPassword"]')).nativeElement.textContent).toContain('Password');
    });
  });

  it('should have "Submit" button', () => {
    fixture.whenStable().then(() => { // wait for async getQuote
      fixture.detectChanges();        // update view with quote
      expect(fixture.debugElement.query(By.css('button[type="submit"]')).nativeElement.textContent).toContain('Submit');
    });
  });
});