/* tslint:disable:no-unused-variable */

import { TestBed, async, ComponentFixture } from '@angular/core/testing';
import { NavbarComponent } from './navbar.component';
import { By } from '@angular/platform-browser';
import { ApiService } from '../../services/api.service';
import { FromUnixPipe, DateFormatPipe } from 'angular2-moment';
import { CapitalizePipe } from '../../pipes/capitalize.pipe';
import { RouterLinkStubDirective } from '../../testing/router-stubs';
import { RouterLinkActive, } from '@angular/router';
import { Router } from '@angular/router';

let comp:    NavbarComponent;
let fixture: ComponentFixture<NavbarComponent>;

describe('Component: Navbar', () => {
  let apiServiceStub = {
    isUserLoggedIn: () => true
  };

  let routerStub = {
    navigateByUrl: (url: string) => true
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [
        RouterLinkActive,
        RouterLinkStubDirective,
        NavbarComponent,
        CapitalizePipe,
        FromUnixPipe,
        DateFormatPipe
      ], // declare the test component
      providers: [
        {provide: Router, useValue: routerStub },
        {provide: ApiService, useValue: apiServiceStub }
      ]
    });

    fixture = TestBed.createComponent(NavbarComponent);

    comp = fixture.componentInstance; // BannerComponent test instance

    let apiService = TestBed.get(ApiService);
  });

  it('should create an instance', () => {
    expect(fixture).toBeTruthy();
  });

  it('should have title "Zoe"', () => {
    expect(fixture.debugElement.query(By.css('nav a.navbar-brand')).nativeElement.textContent).toContain('Zoe');
  });

  it('should have the toggle for small screen', () => {
    expect(fixture.debugElement.query(By.css('span.sr-only')).nativeElement.textContent).toContain('Toggle navigation');
  });

  it('should have 3 links', () => {
    fixture.whenStable().then(() => { // wait for async getQuote
      fixture.detectChanges();        // update view with quote
      let links = fixture.debugElement.queryAll(By.css('a'))
      console.log(links.length)
      expect(links.length).toBe(3);

      let link1 = links[0]
      console.log(link1)
      let link2 = links[1]
      console.log(link2)
      let link3 = links[2]
      console.log(link3)
    });
  });
});