import { Injectable } from '@angular/core'
import {Headers} from "@angular/http";

let AUTH_HEADER: string = 'authHeader'
let USERNAME: string = 'username'

@Injectable()
export class StorageService {
  setAuthHeader(headers: Headers) {
    localStorage.setItem(AUTH_HEADER, headers.get("authorization"))
  }

  getAuthHeader(): Headers {
    let auth = localStorage.getItem(AUTH_HEADER)
    if (auth == null)
      return null
    
    var headers = new Headers
    headers.append('Authorization', auth)
    return headers
  }

  removeAuthHeader() {
    localStorage.removeItem(AUTH_HEADER)
  }

  setUsername(username: string) {
    localStorage.setItem(USERNAME, username)
  }

  getUsername(): string {
    return localStorage.getItem(USERNAME)
  }

  removeUsername() {
    localStorage.removeItem(USERNAME)
  }
}

export class StorageServiceStub extends StorageService {
  private headers: Headers;
  private username: string;

  constructor(
      headers: Headers,
      username: string
  ) {
    super()
    this.headers = headers;
    this.username = username;
  }

  setAuthHeader(headers: Headers) { this.headers = headers }
  getAuthHeader(): Headers { return this.headers }
  removeAuthHeader() { this.headers = null }

  setUsername(username: string) { this.username = username}
  getUsername(): string { return this.username }
  removeUsername() { this.username = null }
}