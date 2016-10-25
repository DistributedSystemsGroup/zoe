/* tslint:disable:no-unused-variable */

import { TestBed, async } from '@angular/core/testing';
import { LoginComponent } from './login.component';

describe('Component: Login', () => {
  it('should create an instance', () => {
    let component = new LoginComponent();
    expect(component).toBeTruthy();
  });

  it('should have title "Login"', () => {
    let component = new LoginComponent();
    expect(component).toBeTruthy();
    let compiled = component.debugElement.nativeElement;
    expect(compiled.querySelector('h1').textContent).toContain('Login');
  });

  it('should have "Username" input field', () => {
    let component = new LoginComponent();
    let compiled = component.debugElement.nativeElement;
    expect(compiled.querySelector('label[for="inputUsername"]').textContent).toContain('Username');
  });

  it('should have "Password" input field', () => {
    let component = new LoginComponent();
    let compiled = component.debugElement.nativeElement;
    expect(compiled.querySelector('label[for="inputPassword"]').textContent).toContain('Password');
  });

  it('should have "Submit" button', () => {
    let component = new LoginComponent();
    let compiled = component.debugElement.nativeElement;
    expect(compiled.querySelector('button[type="submit"]').textContent).toContain('Submit');
  });
});
