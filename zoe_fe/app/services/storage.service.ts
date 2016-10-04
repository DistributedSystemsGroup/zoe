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
        var headers = new Headers
        headers.append('Authorization', localStorage.getItem(AUTH_HEADER))
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