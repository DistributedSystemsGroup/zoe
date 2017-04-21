/* tslint:disable:no-unused-variable */

import { TestBed, async, inject } from '@angular/core/testing';
import { StorageService } from './storage.service';
import { Headers } from "@angular/http";

let AUTH_HEADER = randomString();
let USERNAME = randomString();

function randomString()
{
  var text = "";
  var possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";

  for( var i=0; i < 5; i++ )
    text += possible.charAt(Math.floor(Math.random() * possible.length));

  return text;
}

describe('Service: Storage', () => {
  let service: StorageService;

  let header = new Headers();
  header.append('Authorization', AUTH_HEADER)

  beforeEach(() => { service = new StorageService(); });

  it('#getAuthHeader should return the value set with #setAuthHeader', () => {
    service.setAuthHeader(header)
    expect(service.getAuthHeader().get("authorization")).toBe(header.get("authorization"));
  });

  it('#getAuthHeader should return null after #removeAuthHeader', () => {
    service.removeAuthHeader()
    expect(service.getAuthHeader()).toBeNull();
  });

  it('#getUsername should return the value set with #setUsername', () => {
    service.setUsername(USERNAME)
    expect(service.getUsername()).toBe(USERNAME);
  });

  it('#getUsername should return null after #removeUsername', () => {
    service.removeUsername()
    expect(service.getUsername()).toBeNull();
  });
});
