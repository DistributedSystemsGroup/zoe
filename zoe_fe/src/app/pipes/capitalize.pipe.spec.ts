/* tslint:disable:no-unused-variable */

import { TestBed, async } from '@angular/core/testing';
import { CapitalizePipe } from './capitalize.pipe';

describe('Pipe: Capitalize', () => {
  let pipe = new CapitalizePipe();

  it('Transform "abc" to "Abc"', () => {
    expect(pipe.transform('abc')).toBe('Abc');
  });

  it('Transform "Abc" to "Abc"', () => {
    expect(pipe.transform('Abc')).toBe('Abc');
  });

  it('Transform "aBc" to "ABc"', () => {
    expect(pipe.transform('aBc')).toBe('ABc');
  });
});
