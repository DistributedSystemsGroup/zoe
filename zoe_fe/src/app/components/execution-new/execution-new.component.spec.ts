/* tslint:disable:no-unused-variable */

import { TestBed, async } from '@angular/core/testing';
import { ExecutionNewComponent } from './execution-new.component';

describe('Component: ExecutionNew', () => {
  it('should create an instance', () => {
    let component = new ExecutionNewComponent();
    expect(component).toBeTruthy();
  });

  it('should have "Name" input field', () => {
    let component = new ExecutionNewComponent();
    let compiled = component.debugElement.nativeElement;
    expect(compiled.querySelector('label[for="inputName"]').textContent).toContain('Name');
  });

  it('should have "Description" input field', () => {
    let component = new ExecutionNewComponent();
    let compiled = component.debugElement.nativeElement;
    expect(compiled.querySelector('label[for="inputDescription"]').textContent).toContain('Description');
  });

  it('should have "Submit" button', () => {
    let component = new ExecutionNewComponent();
    let compiled = component.debugElement.nativeElement;
    expect(compiled.querySelector('button[type="submit"]').textContent).toContain('Submit');
  });
});
