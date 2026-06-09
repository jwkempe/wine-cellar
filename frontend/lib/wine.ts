import { Bottle } from './api'

/** A bottle is ready when the current year falls inside its drink window. */
export function isReady(bottle: Bottle): boolean {
  const year = new Date().getFullYear()
  return bottle.drink_from !== null && bottle.drink_by !== null &&
    year >= bottle.drink_from && year <= bottle.drink_by
}
