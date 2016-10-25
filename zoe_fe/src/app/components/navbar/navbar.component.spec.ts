/* tslint:disable:no-unused-variable */

import { TestBed, async } from '@angular/core/testing';
import { NavbarComponent } from './navbar.component';

describe('Component: Navbar', () => {
  it('should create an instance', () => {
    let component = new NavbarComponent();
    expect(component).toBeTruthy();
  });

  it('should have title "Zoe"', () => {
    let component = new LoginComponent();
    expect(component).toBeTruthy();
    let compiled = component.debugElement.nativeElement;
    expect(compiled.querySelector('nav a.navbar-brand').textContent).toContain('Zoe');
  });

  it('should have the toggle for small screen', () => {
    let component = new LoginComponent();
    let compiled = component.debugElement.nativeElement;
    expect(compiled.querySelector('span.sr-only').textContent).toContain('Toggle navigation');
  });

  it('should have the "Executlions List" link', () => {
    let component = new LoginComponent();
    let compiled = component.debugElement.nativeElement;
    expect(compiled.querySelector('a[href="/executions/list"]').textContent).toContain('Executions list');
  });

  it('should have the "New Execution" link', () => {
    let component = new LoginComponent();
    let compiled = component.debugElement.nativeElement;
    expect(compiled.querySelector('a[href="/executions/new"]').textContent).toContain('New Execution');
  });
});
